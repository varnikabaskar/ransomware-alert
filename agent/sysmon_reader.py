from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET


EVENT_FILE_CREATE = 11
EVENT_PROCESS_CREATE = 1
EVENT_PROCESS_ACCESS = 10
EVENT_REGISTRY_EVENT_IDS = {12, 13, 14}


def read_sysmon_events(sysmon_xml_path: str, limit: int = 50) -> list[dict]:
    if not sysmon_xml_path:
        return []

    path = Path(sysmon_xml_path)
    if not path.exists() or path.is_dir():
        return []

    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except ET.ParseError:
        return []

    events: list[dict] = []
    for event in root.findall(".//Event")[:limit]:
        process_name = "unknown"
        event_id = 0
        timestamp = None

        system = event.find("System")
        if system is not None:
            event_id_node = system.find("EventID")
            try:
                event_id = int((event_id_node.text or "0")) if event_id_node is not None else 0
            except ValueError:
                event_id = 0

            time_created = system.find("TimeCreated")
            if time_created is not None:
                timestamp = time_created.attrib.get("SystemTime")

        event_data = event.find("EventData")
        command_line = ""
        user = ""
        if event_data is not None:
            for data in event_data.findall("Data"):
                name = data.attrib.get("Name")
                value = data.text or ""
                if name == "Image":
                    process_name = (data.text or "unknown").split("\\")[-1]
                elif name == "CommandLine":
                    command_line = value
                elif name in {"User", "UserName"}:
                    user = value

        suspicious_cli = 1.0 if any(k in command_line.lower() for k in ["vssadmin", "wbadmin", "bcdedit", "cipher", "shadowcopy"]) else 0.0
        registry_flag = 1.0 if event_id in EVENT_REGISTRY_EVENT_IDS else 0.0
        file_flag = 1.0 if event_id == EVENT_FILE_CREATE else 0.0
        proc_flag = 1.0 if event_id in {EVENT_PROCESS_CREATE, EVENT_PROCESS_ACCESS} else 0.0
        priv_flag = 1.0 if any(u in user.lower() for u in ["system", "admin", "administrator"]) else 0.0

        events.append(
            {
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
                "process_name": process_name,
                "file_ops_per_min": min(1.0, (0.35 * file_flag) + (0.25 * proc_flag)),
                "entropy_delta": min(1.0, (0.45 * suspicious_cli) + (0.25 * registry_flag) + (0.20 * file_flag)),
                "extension_change_rate": min(1.0, (0.40 * file_flag) + (0.30 * suspicious_cli)),
                "failed_decrypt_ops": min(1.0, (0.45 * suspicious_cli) + (0.20 * proc_flag)),
                "shadow_copy_delete_attempt": suspicious_cli,
                "privilege_escalation_flag": min(1.0, (0.55 * priv_flag) + (0.20 * suspicious_cli)),
            }
        )

    return events
