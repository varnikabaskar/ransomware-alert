from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EventFeature(BaseModel):
    timestamp: datetime
    process_name: str
    file_ops_per_min: float = 0.0
    entropy_delta: float = 0.0
    extension_change_rate: float = 0.0
    failed_decrypt_ops: float = 0.0
    shadow_copy_delete_attempt: float = 0.0
    privilege_escalation_flag: float = 0.0


class AgentHeartbeat(BaseModel):
    agent_id: str
    host: str
    ip_address: str
    sysmon_enabled: bool
    events: list[EventFeature] = Field(default_factory=list)
    trap_events: list[dict[str, Any]] = Field(default_factory=list)


class AgentSummary(BaseModel):
    agent_id: str
    host: str
    ip_address: str
    sysmon_enabled: bool
    last_seen: datetime
    event_count: int = 0
    trap_event_count: int = 0


class DetectionRequest(BaseModel):
    agent_id: str
    host: str
    events: list[EventFeature] = Field(default_factory=list)
    trap_events: list[dict[str, Any]] = Field(default_factory=list)


class DetectionResult(BaseModel):
    agent_id: str
    host: str
    behavioral_score: float
    decoy_score: float
    risk_score: float
    severity: str = "normal"
    is_ransomware: bool
    reasons: list[str]
    suspected_processes: list[str] = Field(default_factory=list)
    timestamp: datetime


class AlertRecord(BaseModel):
    id: str
    level: str
    message: str
    result: DetectionResult
    created_at: datetime
    contained: bool = False
    containment_notes: str | None = None
    acknowledged: bool = False


class TrainRequest(BaseModel):
    behavioral_csv_path: str
    decoy_csv_path: str
    sequence_length: int = 20
    epochs: int = 60
    test_size: float = 0.2
    random_state: int = 42
