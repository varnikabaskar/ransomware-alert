from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import random
from threading import Lock

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from ml.decoy.placement import strategized_decoy_placement


class _DecoyEventHandler(FileSystemEventHandler):
    def __init__(self, sink: list[dict], sink_lock: Lock) -> None:
        self.sink = sink
        self.sink_lock = sink_lock

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if not path.name.startswith("DEC0Y_"):
            return

        with self.sink_lock:
            self.sink.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "file": str(path),
                    "access_freq": random.uniform(0.3, 1.0),
                    "rename_burst": 1.0 if event.event_type == "moved" else random.uniform(0.0, 0.7),
                    "entropy_jump": random.uniform(0.2, 0.9),
                    "unknown_process_touch": random.choice([0.0, 1.0]),
                }
            )


class DecoyMonitor:
    def __init__(self, watch_dir: str) -> None:
        self.watch_dir = Path(watch_dir)
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        self._events: list[dict] = []
        self._lock = Lock()
        self._observer = Observer()
        self._manifest_path = self.watch_dir / ".decoy_manifest.json"

    def _candidate_files(self, limit: int = 500) -> tuple[list[str], list[int], list[int]]:
        files = []
        sizes = []
        depths = []
        for p in self.watch_dir.rglob("*"):
            if len(files) >= limit:
                break
            if not p.is_file() or p.name.startswith("DEC0Y_"):
                continue
            rel = p.relative_to(self.watch_dir)
            files.append(str(p))
            sizes.append(int(p.stat().st_size))
            depths.append(len(rel.parts))
        return files, sizes, depths

    def _load_manifest(self) -> dict:
        if not self._manifest_path.exists():
            return {}
        try:
            return json.loads(self._manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_manifest(self, paths: list[str]) -> None:
        wiretraps = {}
        for p in paths:
            path = Path(p)
            if not path.exists() or not path.is_file():
                continue
            content = path.read_bytes()
            wiretraps[str(path)] = {
                "sha256": hashlib.sha256(content).hexdigest(),
                "size": len(content),
            }
        payload = {
            "last_rotation_utc": datetime.now(timezone.utc).isoformat(),
            "paths": paths,
            "wiretraps": wiretraps,
        }
        self._manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _rotation_due(self, days: int = 30) -> bool:
        manifest = self._load_manifest()
        raw = manifest.get("last_rotation_utc")
        if not raw:
            return True
        try:
            then = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            return True
        delta = datetime.now(timezone.utc) - then.astimezone(timezone.utc)
        return delta.days >= days

    def _cleanup_old_decoys(self) -> None:
        for p in self.watch_dir.rglob("DEC0Y_*"):
            if p.is_file():
                try:
                    p.unlink(missing_ok=True)
                except OSError:
                    continue

    def rotate_if_due(self, count: int = 12) -> list[str]:
        if not self._rotation_due(days=30):
            return []
        self._cleanup_old_decoys()
        return self.setup_decoys(count=count)

    def setup_decoys(self, count: int = 12) -> list[str]:
        files, sizes, depths = self._candidate_files()
        preferred = strategized_decoy_placement(files, sizes, depths)
        preferred_dirs = [str(Path(p).parent) for p in preferred]
        if not preferred_dirs:
            preferred_dirs = [str(self.watch_dir)]

        created = []
        for i in range(count):
            target_dir = Path(preferred_dirs[i % len(preferred_dirs)])
            target_dir.mkdir(parents=True, exist_ok=True)
            fpath = target_dir / f"DEC0Y_finance_{i:02d}.xlsx"
            if not fpath.exists():
                canary = f"WIRETRAP::{datetime.now(timezone.utc).isoformat()}::{i:02d}"
                fpath.write_text(
                    "confidential: budget projections\n"
                    "owner: finance\n"
                    f"canary: {canary}\n",
                    encoding="utf-8",
                )
            created.append(str(fpath))
        self._save_manifest(created)
        return created

    def collect_wiretrap_alerts(self) -> list[dict]:
        manifest = self._load_manifest()
        tracked = manifest.get("wiretraps", {}) if isinstance(manifest, dict) else {}
        if not tracked:
            return []

        now = datetime.now(timezone.utc).isoformat()
        alerts = []
        for p, meta in tracked.items():
            path = Path(p)
            if not path.exists() or not path.is_file():
                alerts.append(
                    {
                        "timestamp": now,
                        "file": str(path),
                        "access_freq": 1.0,
                        "rename_burst": 1.0,
                        "entropy_jump": 1.0,
                        "unknown_process_touch": 1.0,
                        "wiretrap_event": "missing_or_deleted",
                    }
                )
                continue

            content = path.read_bytes()
            current_hash = hashlib.sha256(content).hexdigest()
            original_hash = str(meta.get("sha256", ""))
            if original_hash and current_hash != original_hash:
                alerts.append(
                    {
                        "timestamp": now,
                        "file": str(path),
                        "access_freq": 1.0,
                        "rename_burst": 0.9,
                        "entropy_jump": 0.95,
                        "unknown_process_touch": 1.0,
                        "wiretrap_event": "content_tamper",
                    }
                )

        return alerts

    def start(self) -> None:
        handler = _DecoyEventHandler(self._events, self._lock)
        self._observer.schedule(handler, str(self.watch_dir), recursive=True)
        self._observer.start()

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join(timeout=5)

    def drain_events(self) -> list[dict]:
        with self._lock:
            payload = list(self._events)
            self._events.clear()
        return payload
