from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path

import psutil
import requests
import yaml

from agent.collector import collect_behavioral_events
from agent.decoy_monitor import DecoyMonitor
from agent.notifier import AgentNotifier
from agent.sysmon_reader import read_sysmon_events


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="R-GUARD endpoint monitoring agent")
    parser.add_argument("--config", default="agent/config.example.yaml", help="Path to YAML config")
    return parser.parse_args()


def _write_runtime_status(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _terminate_local_processes(process_names: list[str]) -> list[str]:
    targets = {p.lower() for p in process_names if p}
    if not targets:
        return []

    allowlist = {
        "system",
        "svchost.exe",
        "services.exe",
        "explorer.exe",
        "python.exe",
        "powershell.exe",
        "pwsh.exe",
        "cmd.exe",
        "code.exe",
        "uvicorn.exe",
    }

    terminated = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = (proc.info.get("name") or "").lower()
            if name in allowlist:
                continue
            if name and name in targets:
                proc.terminate()
                terminated.append(f"{name}:{proc.info.get('pid')}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return terminated


def main() -> None:
    args = parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    server_url = cfg["server_url"].rstrip("/")
    api_token = str(cfg.get("api_token", "")).strip()
    agent_id = cfg["agent_id"]
    pass_key = str(cfg.get("pass_key", "")).strip()
    poll_seconds = int(cfg.get("poll_seconds", 10))
    sysmon_path = cfg.get("sysmon_xml_path", "")
    notify_every = int(cfg.get("notify_every_cycles", 6))
    popup_threshold = float(cfg.get("popup_risk_threshold", 0.90))
    local_termination = bool(cfg.get("enable_local_termination", True))
    status_path = Path(cfg.get("runtime_status_path", "agent/runtime_status.json"))

    monitor = DecoyMonitor(cfg.get("decoy_watch_dir", "agent/decoy_files"))
    monitor.setup_decoys(count=int(cfg.get("decoy_count", 12)))
    monitor.start()
    notifier = AgentNotifier(log_path=str(Path("agent") / "notifications.log"))

    host = socket.gethostname()
    ip_address = socket.gethostbyname(host)
    cycle = 0
    recent_logs: list[dict] = []
    recent_alerts: list[dict] = []
    recent_notifications: list[dict] = []
    last_critical_notify_time = 0.0  # Track time of last critical alert to avoid duplicate popups
    last_critical_fingerprint: str | None = None

    print(f"[R-GUARD Agent] Started as {agent_id} on {host}")
    notifier.notify_info("R-GUARD Agent", f"Monitoring started on host {host}")

    if pass_key:
        headers = {"X-Agent-Id": agent_id, "X-Agent-Key": pass_key}
    else:
        headers = {"X-R-Guard-Token": api_token} if api_token else None

    try:
        while True:
            # allow dynamic runtime config updates (e.g., pass_key written by local dashboard)
            runtime_cfg_path = Path("agent/runtime_config.json")
            if runtime_cfg_path.exists():
                try:
                    rcfg = json.loads(runtime_cfg_path.read_text(encoding="utf-8"))
                    new_key = str(rcfg.get("pass_key", "")).strip()
                    if new_key and new_key != pass_key:
                        pass_key = new_key
                        headers = {"X-Agent-Id": agent_id, "X-Agent-Key": pass_key}
                except Exception:
                    # ignore corrupt runtime config
                    pass
            cycle += 1
            rotated = monitor.rotate_if_due(count=int(cfg.get("decoy_count", 12)))
            if rotated:
                msg = f"Decoy placement rotated ({len(rotated)} files)"
                notifier.notify_info("R-GUARD Decoys", msg)
                recent_notifications.insert(0, {"level": "info", "message": msg, "timestamp": time.time()})

            events = collect_behavioral_events(max_events=25)
            sysmon_events = read_sysmon_events(sysmon_path, limit=20)
            if sysmon_events:
                events.extend(sysmon_events)

            trap_events = monitor.drain_events()
            trap_events.extend(monitor.collect_wiretrap_alerts())

            heartbeat_payload = {
                "agent_id": agent_id,
                "host": host,
                "ip_address": ip_address,
                "sysmon_enabled": bool(sysmon_path),
                "events": events,
                "trap_events": trap_events,
            }
            requests.post(f"{server_url}/agent/heartbeat", json=heartbeat_payload, headers=headers, timeout=20)

            detect_payload = {
                "agent_id": agent_id,
                "host": host,
                "events": events,
                "trap_events": trap_events,
            }
            resp = requests.post(f"{server_url}/agent/detect", json=detect_payload, headers=headers, timeout=30)
            verdict = resp.json()

            risk = float(verdict.get("risk_score", 0.0))
            severity = str(verdict.get("severity", "normal"))
            suspects = verdict.get("suspected_processes", [])

            # Send periodic informational notifications only for warnings (not for criticals)
            if severity == "warning" and cycle % max(1, notify_every) == 0:
                msg = f"Risk {risk:.2f} on {host} (severity: {severity})"
                notifier.notify_info("R-GUARD Monitoring", msg)
                recent_notifications.insert(0, {"level": "info", "message": msg, "timestamp": time.time()})

            if verdict.get("is_ransomware", False) or risk >= popup_threshold:
                msg = f"High risk detected on {host}. score={risk:.2f}"
                # Compute a simple fingerprint for this critical condition so we don't spam
                suspects_list = ",".join(sorted([str(s) for s in suspects])) if suspects else ""
                fingerprint = f"{verdict.get('is_ransomware', False)}|{severity}|{int(risk*100)}|{suspects_list}"
                # record last seen fingerprint to avoid repeating the same notification each cycle
                last_critical_fingerprint = fingerprint
                current_time = time.time()
                # Suppress repeated popups for the same fingerprint. Allow a short cooldown (60s)
                # and a longer suppression window (300s) for identical fingerprints.
                cooldown = 60.0
                long_suppression = 300.0
                should_notify = False
                if last_critical_fingerprint != fingerprint:
                    should_notify = True
                else:
                    # same fingerprint as last time; only notify if long_suppression elapsed
                    if current_time - last_critical_notify_time >= long_suppression:
                        should_notify = True

                if should_notify and (current_time - last_critical_notify_time >= cooldown):
                    notifier.notify_critical("R-GUARD Critical Alert", msg)
                    last_critical_notify_time = current_time
                terminated = []
                if local_termination:
                    terminated = _terminate_local_processes([str(p) for p in suspects])
                alert = {
                    "timestamp": time.time(),
                    "risk": risk,
                    "severity": severity,
                    "suspected_processes": suspects,
                    "terminated": terminated,
                }
                recent_alerts.insert(0, alert)
                recent_notifications.insert(0, {"level": "critical", "message": msg, "timestamp": time.time(), "fingerprint": last_critical_fingerprint})

            print(
                "[R-GUARD Agent] risk=",
                f"{risk:.3f}",
                "behavior=",
                f"{verdict.get('behavioral_score', 0):.3f}",
                "decoy=",
                f"{verdict.get('decoy_score', 0):.3f}",
                "alert=",
                verdict.get("is_ransomware", False),
            )

            recent_logs.insert(
                0,
                {
                    "timestamp": time.time(),
                    "risk": risk,
                    "severity": severity,
                    "events": len(events),
                    "trap_events": len(trap_events),
                },
            )

            recent_logs = recent_logs[:50]
            recent_alerts = recent_alerts[:50]
            recent_notifications = recent_notifications[:100]
            _write_runtime_status(
                status_path,
                {
                    "agent_id": agent_id,
                    "host": host,
                    "ip_address": ip_address,
                    "poll_seconds": poll_seconds,
                    "last_cycle": cycle,
                    "last_verdict": verdict,
                    "logs": recent_logs,
                    "alerts": recent_alerts,
                    "notifications": recent_notifications,
                    "health": {
                        "sysmon_enabled": bool(sysmon_path),
                        "decoy_watch_dir": cfg.get("decoy_watch_dir", "agent/decoy_files"),
                    },
                },
            )
            time.sleep(poll_seconds)
    finally:
        monitor.stop()


if __name__ == "__main__":
    main()
