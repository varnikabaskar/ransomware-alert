import psutil

from server.app.config import settings


class ContainmentService:
    def terminate_suspect_processes(self, process_names: list[str]) -> tuple[bool, str]:
        allowlist = {n.strip().lower() for n in settings.containment_allowlist.split(",") if n.strip()}
        killed: list[str] = []
        targets = {n.lower() for n in process_names if n}
        if not targets:
            return False, "No target process provided for containment."

        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if name in allowlist:
                    continue
                if name in targets:
                    proc.terminate()
                    killed.append(f"{name}:{proc.info.get('pid')}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed:
            return True, f"Terminated suspect process(es): {', '.join(killed)}"
        return False, "No target process terminated. Manual isolation recommended."
