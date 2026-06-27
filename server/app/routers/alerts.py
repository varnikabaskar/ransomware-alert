from fastapi import APIRouter, Depends, HTTPException, Query

from server.app.dependencies import get_alert_store, verify_dashboard_token

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def list_alerts(
    _=Depends(verify_dashboard_token),
    store=Depends(get_alert_store),
    unread_critical_only: bool = Query(False),
    host: str | None = Query(None),
):
    """Get alerts. If `unread_critical_only=true`, return unread critical alerts only (up to 10).
    Optional `host` filters the results to a single agent host."""
    alerts = store.list_alerts(host=host)

    if unread_critical_only:
        # Return only unread critical alerts, limited to 10
        notifications = []
        for a in alerts:
            if a.get("acknowledged") is False and a.get("level") == "critical":
                result = a.get("result", {})
                notifications.append({
                    "id": a.get("id", "unknown"),
                    "level": "critical",
                    "message": a.get("message", "Critical alert triggered"),
                    "timestamp": a.get("created_at", ""),
                    "affectedSystem": result.get("host", "unknown"),
                })
        return notifications[:10]

    return alerts


@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, _=Depends(verify_dashboard_token), store=Depends(get_alert_store)):
    if not store.mark_acknowledged(alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "ok", "alert_id": alert_id, "acknowledged": True}
