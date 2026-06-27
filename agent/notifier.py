from __future__ import annotations

import ctypes
from datetime import datetime, timezone
from pathlib import Path


try:
    from win10toast import ToastNotifier
except Exception:
    ToastNotifier = None


class AgentNotifier:
    def __init__(self, log_path: str = "agent/notifications.log") -> None:
        self._toast = ToastNotifier() if ToastNotifier is not None else None
        self._log_path = Path(log_path)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def _log(self, level: str, title: str, message: str) -> None:
        line = f"{datetime.now(timezone.utc).isoformat()} | {level.upper()} | {title} | {message}\n"
        with self._log_path.open("a", encoding="utf-8") as f:
            f.write(line)

    def notify_info(self, title: str, message: str) -> None:
        self._log("info", title, message)
        if self._toast is not None:
            try:
                self._toast.show_toast(title, message, duration=4, threaded=True)
            except Exception:
                pass

    def notify_critical(self, title: str, message: str) -> None:
        self._log("critical", title, message)
        if self._toast is not None:
            try:
                self._toast.show_toast(title, message, duration=8, threaded=True)
            except Exception:
                pass
        try:
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x00001000)
        except Exception:
            pass
