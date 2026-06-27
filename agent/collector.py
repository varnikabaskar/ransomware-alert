from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import psutil


SUSPICIOUS_PROCESS_KEYWORDS = {
    "vssadmin",
    "wbadmin",
    "bcdedit",
    "cipher",
    "powershell",
    "wmic",
    "rundll32",
    "cmd",
}


def _bounded(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return float(min(max(value / max_value, 0.0), 1.0))


def _suspicious_name_score(name: str) -> float:
    lowered = (name or "").lower()
    return 1.0 if any(k in lowered for k in SUSPICIOUS_PROCESS_KEYWORDS) else 0.0


def collect_behavioral_events(max_events: int = 25) -> list[dict]:
    events: list[dict] = []
    for proc in psutil.process_iter(["name", "io_counters"]):
        if len(events) >= max_events:
            break
        try:
            io_stats = proc.info.get("io_counters")
            read_count = float(getattr(io_stats, "read_count", 0.0))
            write_count = float(getattr(io_stats, "write_count", 0.0))
            read_bytes = float(getattr(io_stats, "read_bytes", 0.0))
            write_bytes = float(getattr(io_stats, "write_bytes", 0.0))

            total_ops = read_count + write_count
            file_ops = _bounded(total_ops, 4000.0)
            write_ratio = (write_count / max(1.0, total_ops))
            byte_ratio = (write_bytes / max(1.0, read_bytes + write_bytes))
            process_name = proc.info.get("name") or "unknown"
            suspicious_name = _suspicious_name_score(process_name)

            events.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "process_name": process_name,
                    "file_ops_per_min": file_ops,
                    "entropy_delta": float(np.clip((0.55 * write_ratio) + (0.45 * byte_ratio), 0.0, 1.0)),
                    "extension_change_rate": float(np.clip((0.70 * write_ratio) + (0.30 * suspicious_name), 0.0, 1.0)),
                    "failed_decrypt_ops": float(np.clip((0.35 * suspicious_name) + (0.25 * file_ops), 0.0, 1.0)),
                    "shadow_copy_delete_attempt": float(suspicious_name),
                    "privilege_escalation_flag": float(suspicious_name),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return events
