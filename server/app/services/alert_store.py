import json
import threading
from pathlib import Path

from server.app.schemas import AlertRecord


class AlertStore:
    def __init__(self, file_path: str) -> None:
        self._file_path = Path(file_path)
        self._lock = threading.Lock()
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._file_path.exists():
            self._file_path.write_text("[]", encoding="utf-8")

    def list_alerts(self, host: str | None = None) -> list[AlertRecord]:
        with self._lock:
            payload = json.loads(self._file_path.read_text(encoding="utf-8"))
        alerts = [AlertRecord.model_validate(item) for item in payload]
        if host:
            alerts = [alert for alert in alerts if (alert.result.host or "") == host]
        return alerts

    def list_hosts(self) -> list[str]:
        with self._lock:
            payload = json.loads(self._file_path.read_text(encoding="utf-8"))
        hosts = []
        for item in payload:
            host = ((item.get("result") or {}).get("host") or "").strip()
            if host and host not in hosts:
                hosts.append(host)
        return hosts

    def append_alert(self, alert: AlertRecord) -> None:
        with self._lock:
            payload = json.loads(self._file_path.read_text(encoding="utf-8"))
            payload.insert(0, alert.model_dump(mode="json"))
            payload = payload[:500]
            self._file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def mark_acknowledged(self, alert_id: str) -> bool:
        with self._lock:
            payload = json.loads(self._file_path.read_text(encoding="utf-8"))
            changed = False
            for item in payload:
                if item["id"] == alert_id:
                    item["acknowledged"] = True
                    changed = True
                    break
            if changed:
                self._file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return changed

    def mark_contained(self, alert_id: str, notes: str) -> bool:
        with self._lock:
            payload = json.loads(self._file_path.read_text(encoding="utf-8"))
            changed = False
            for item in payload:
                if item["id"] == alert_id:
                    item["contained"] = True
                    item["containment_notes"] = notes
                    changed = True
                    break
            if changed:
                self._file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return changed
