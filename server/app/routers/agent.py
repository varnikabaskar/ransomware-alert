import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from server.app.config import settings
from server.app.dependencies import get_agent_store, get_alert_store, get_containment_service, get_inference_service, verify_api_token
from server.app.dependencies import verify_dashboard_token
from server.app.schemas import AgentHeartbeat, AgentSummary, AlertRecord, DetectionRequest

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/heartbeat")
def heartbeat(payload: AgentHeartbeat, _=Depends(verify_api_token)):
    get_agent_store().upsert_agent(payload)
    return {
        "status": "received",
        "agent_id": payload.agent_id,
        "events": len(payload.events),
        "trap_events": len(payload.trap_events),
    }


@router.get("/agents", response_model=list[AgentSummary])
def list_agents(_=Depends(verify_api_token), store=Depends(get_agent_store)):
    return store.list_agents()


@router.post("/detect")
def detect(
    payload: DetectionRequest,
    _=Depends(verify_api_token),
    inference=Depends(get_inference_service),
    store=Depends(get_alert_store),
    containment=Depends(get_containment_service),
):
    result = inference.detect(payload)

    if result.is_ransomware:
        message = f"Possible ransomware activity on host {payload.host}"
        alert = AlertRecord(
            id=str(uuid.uuid4()),
            level="critical",
            message=message,
            result=result,
            created_at=datetime.now(timezone.utc),
        )
        if settings.enable_containment:
            process_names = list(result.suspected_processes) or [e.process_name for e in payload.events if e.process_name]
            contained, notes = containment.terminate_suspect_processes(process_names)
            alert.contained = contained
            alert.containment_notes = notes
        store.append_alert(alert)

    return result


@router.post("/register/generate")
def generate_registration_code(_=Depends(verify_dashboard_token), store=Depends(get_agent_store)):
    """Admin endpoint: generate a single-use registration code for an agent."""
    code = store.generate_registration_code()
    return {"code": code}


@router.post("/register/confirm")
def confirm_registration(payload: dict, store=Depends(get_agent_store)):
    """Agent submits a registration code along with its agent_id to bind to the server.

    Payload expected: {"agent_id": "<id>", "code": "<registration-code>"}
    """
    agent_id = payload.get("agent_id")
    code = payload.get("code")
    if not agent_id or not code:
        raise HTTPException(status_code=400, detail="agent_id and code are required")

    valid = store.validate_and_consume_code(code)
    if not valid:
        raise HTTPException(status_code=400, detail="Invalid or expired registration code")

    # bind the code as the agent passkey
    store.set_agent_passkey(agent_id, code)
    # return the assigned pass_key so the agent UI can persist it locally
    return {"status": "registered", "agent_id": agent_id, "pass_key": code}


@router.delete("/agents/{agent_id}")
def delete_agent(agent_id: str, _=Depends(verify_dashboard_token), store=Depends(get_agent_store)):
    store.remove_agent(agent_id)
    return {"status": "removed", "agent_id": agent_id}
