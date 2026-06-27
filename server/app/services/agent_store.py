import json
import threading
from datetime import datetime, timezone
import uuid
from pathlib import Path

from server.app.schemas import AgentHeartbeat, AgentSummary


class AgentStore:
    def __init__(self, file_path: str) -> None:
        self._file_path = Path(file_path)
        self._lock = threading.Lock()
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._file_path.exists():
            self._file_path.write_text("[]", encoding="utf-8")
        # registration codes are stored separately
        self._codes_path = self._file_path.parent / ".agent_codes.json"
        if not self._codes_path.exists():
            self._codes_path.write_text("[]", encoding="utf-8")

    def list_agents(self) -> list[AgentSummary]:
        with self._lock:
            payload = json.loads(self._file_path.read_text(encoding="utf-8"))
        return [AgentSummary.model_validate(item) for item in payload]

    def remove_agent(self, agent_id: str) -> None:
        with self._lock:
            payload = json.loads(self._file_path.read_text(encoding="utf-8"))
            payload = [p for p in payload if p.get("agent_id") != agent_id]
            self._file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def generate_registration_code(self) -> str:
        code = uuid.uuid4().hex[:12].upper()
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            codes = json.loads(self._codes_path.read_text(encoding="utf-8"))
            codes.insert(0, {"code": code, "created_at": now})
            codes = codes[:100]
            self._codes_path.write_text(json.dumps(codes, indent=2), encoding="utf-8")
        return code

    def validate_and_consume_code(self, code: str) -> bool:
        with self._lock:
            codes = json.loads(self._codes_path.read_text(encoding="utf-8"))
            for i, item in enumerate(codes):
                if item.get("code") == code:
                    # consume
                    del codes[i]
                    self._codes_path.write_text(json.dumps(codes, indent=2), encoding="utf-8")
                    return True
        return False

    def set_agent_passkey(self, agent_id: str, passkey: str) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            payload = json.loads(self._file_path.read_text(encoding="utf-8"))
            changed = False
            for item in payload:
                if item.get("agent_id") == agent_id:
                    item.update({"pass_key": passkey, "registered": True, "last_seen": now.isoformat()})
                    changed = True
                    break

            if not changed:
                payload.insert(
                    0,
                    {
                        "agent_id": agent_id,
                        "host": "unknown",
                        "ip_address": None,
                        "sysmon_enabled": False,
                        "last_seen": now.isoformat(),
                        "event_count": 0,
                        "trap_event_count": 0,
                        "pass_key": passkey,
                        "registered": True,
                    },
                )

            payload = payload[:100]
            self._file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def verify_agent_key(self, agent_id: str, key: str) -> bool:
        with self._lock:
            payload = json.loads(self._file_path.read_text(encoding="utf-8"))
            for item in payload:
                if item.get("agent_id") == agent_id and item.get("pass_key") == key:
                    return True
        return False

    def upsert_agent(self, heartbeat: AgentHeartbeat) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            payload = json.loads(self._file_path.read_text(encoding="utf-8"))
            changed = False
            for item in payload:
                if item.get("agent_id") == heartbeat.agent_id:
                    item.update(
                        {
                            "host": heartbeat.host,
                            "ip_address": heartbeat.ip_address,
                            "sysmon_enabled": heartbeat.sysmon_enabled,
                            "last_seen": now.isoformat(),
                            "event_count": len(heartbeat.events),
                            "trap_event_count": len(heartbeat.trap_events),
                        }
                    )
                    changed = True
                    break

            if not changed:
                payload.insert(
                    0,
                    {
                        "agent_id": heartbeat.agent_id,
                        "host": heartbeat.host,
                        "ip_address": heartbeat.ip_address,
                        "sysmon_enabled": heartbeat.sysmon_enabled,
                        "last_seen": now.isoformat(),
                        "event_count": len(heartbeat.events),
                        "trap_event_count": len(heartbeat.trap_events),
                    },
                )

            payload = payload[:100]
            self._file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
