from functools import lru_cache
from typing import Optional

from fastapi import Header, HTTPException, Request

from server.app.config import settings
from server.app.services.agent_store import AgentStore
from server.app.services.alert_store import AlertStore
from server.app.services.containment_service import ContainmentService
from server.app.services.inference_service import InferenceService
from server.app.services.model_registry import ModelRegistry


@lru_cache(maxsize=1)
def get_model_registry() -> ModelRegistry:
    registry = ModelRegistry(model_dir=settings.model_dir)
    registry.load()
    return registry


@lru_cache(maxsize=1)
def get_inference_service() -> InferenceService:
    return InferenceService(models=get_model_registry())


@lru_cache(maxsize=1)
def get_alert_store() -> AlertStore:
    return AlertStore(file_path=settings.alerts_file)


@lru_cache(maxsize=1)
def get_agent_store() -> AgentStore:
    return AgentStore(file_path="server/.agents.json")


@lru_cache(maxsize=1)
def get_containment_service() -> ContainmentService:
    return ContainmentService()


def verify_api_token(x_r_guard_token: Optional[str] = Header(default=None), request = None) -> None:
    """Validate agent/server shared token when secure mode is enabled."""
    if not settings.require_api_token:
        return

    expected = (settings.api_token or "").strip()
    provided = (x_r_guard_token or "").strip()
    if not expected:
        raise HTTPException(status_code=500, detail="API token required but server token is not configured")

    # Accept global server token
    if provided == expected:
        return

    # Fallback: allow per-agent key if present. Agent will send headers: X-Agent-Id and X-Agent-Key
    # Use the agent store to validate per-agent passkey.
    # Note: Request will be injected by FastAPI when available.
    def _bad():
        raise HTTPException(status_code=401, detail="Invalid or missing API token")

    # If global token not provided, allow per-agent keys via headers `X-Agent-Id` and `X-Agent-Key`.
    if request is not None:
        agent_id = request.headers.get("x-agent-id")
        agent_key = request.headers.get("x-agent-key")
        if agent_id and agent_key:
            store = get_agent_store()
            if store.verify_agent_key(agent_id, agent_key):
                return

    _bad()


def verify_dashboard_token(x_r_guard_token: Optional[str] = Header(default=None)) -> None:
    """Optional token gate for dashboard API routes."""
    if not settings.require_dashboard_token:
        return

    expected = (settings.api_token or "").strip()
    provided = (x_r_guard_token or "").strip()
    if not expected:
        raise HTTPException(status_code=500, detail="Dashboard token required but server token is not configured")
    if provided != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing dashboard API token")
