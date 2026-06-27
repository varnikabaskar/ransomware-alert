from dataclasses import dataclass
import os
from pathlib import Path


def _load_project_env() -> None:
    root = Path(__file__).resolve().parents[2]
    env_path = root / ".env"
    if not env_path.exists():
        return

    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


_load_project_env()


@dataclass
class Settings:
    host: str = os.getenv("R_GUARD_SERVER_HOST", "0.0.0.0")
    port: int = int(os.getenv("R_GUARD_SERVER_PORT", "8000"))
    alert_threshold: float = float(os.getenv("R_GUARD_ALERT_THRESHOLD", "0.70"))
    behavioral_weight: float = float(os.getenv("R_GUARD_BEHAVIORAL_WEIGHT", "0.65"))
    decoy_weight: float = float(os.getenv("R_GUARD_DECOY_WEIGHT", "0.35"))
    enable_containment: bool = os.getenv("R_GUARD_ENABLE_CONTAINMENT", "true").lower() == "true"
    api_token: str = os.getenv("R_GUARD_API_TOKEN", "")
    require_api_token: bool = os.getenv("R_GUARD_REQUIRE_API_TOKEN", "false").lower() == "true"
    require_dashboard_token: bool = os.getenv("R_GUARD_REQUIRE_DASHBOARD_TOKEN", "false").lower() == "true"
    containment_allowlist: str = os.getenv(
        "R_GUARD_CONTAINMENT_ALLOWLIST",
        "system,svchost,services,explorer,python,python.exe,powershell,powershell.exe,pwsh,pwsh.exe,cmd,cmd.exe,code,code.exe,uvicorn",
    )
    alerts_file: str = os.getenv("R_GUARD_ALERTS_FILE", "server/.alerts.json")
    model_dir: str = os.getenv("R_GUARD_MODEL_DIR", "models")


settings = Settings()
