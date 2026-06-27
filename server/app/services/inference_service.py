from datetime import datetime, timezone

import numpy as np

from server.app.config import settings
from server.app.schemas import DetectionRequest, DetectionResult
from server.app.services.model_registry import ModelRegistry


class InferenceService:
    def __init__(self, models: ModelRegistry) -> None:
        self.models = models

    def _heuristic_behavior_score(self, event_rows: np.ndarray) -> float:
        if len(event_rows) == 0:
            return 0.0
        weights = np.array([0.25, 0.15, 0.20, 0.15, 0.15, 0.10], dtype=np.float32)
        sample = np.clip(event_rows, 0.0, 1.0)
        per_event = np.dot(sample, weights)
        return float(np.clip(np.mean(per_event), 0.0, 1.0))

    def _heuristic_decoy_score(self, trap_count: int) -> float:
        return float(np.clip(trap_count / 5.0, 0.0, 1.0))

    @staticmethod
    def _event_risk(row: np.ndarray) -> float:
        weights = np.array([0.24, 0.17, 0.18, 0.14, 0.15, 0.12], dtype=np.float32)
        return float(np.clip(np.dot(np.clip(row, 0.0, 1.0), weights), 0.0, 1.0))

    def detect(self, req: DetectionRequest) -> DetectionResult:
        event_rows = np.array(
            [
                [
                    e.file_ops_per_min,
                    e.entropy_delta,
                    e.extension_change_rate,
                    e.failed_decrypt_ops,
                    e.shadow_copy_delete_attempt,
                    e.privilege_escalation_flag,
                ]
                for e in req.events
            ],
            dtype=np.float32,
        )

        suspected_processes: list[str] = []
        if len(event_rows) > 0:
            scores = [self._event_risk(row) for row in event_rows]
            for ev, sc in zip(req.events, scores):
                if sc >= 0.72:
                    suspected_processes.append(ev.process_name)
        # Preserve order, remove duplicates.
        suspected_processes = list(dict.fromkeys([p for p in suspected_processes if p]))

        behavioral_score = 0.0
        if self.models.behavioral_model is not None and len(event_rows) > 0:
            sequence_length = int(getattr(self.models.behavioral_model, "sequence_length", 20))
            if len(event_rows) < sequence_length:
                behavioral_score = self._heuristic_behavior_score(event_rows)
            else:
                raw_prob = float(self.models.behavioral_model.predict_risk(event_rows))
                threshold = float(getattr(self.models.behavioral_model, "decision_threshold", 0.5))
                behavioral_score = float(np.clip((raw_prob - threshold) / max(1e-6, (1.0 - threshold)), 0.0, 1.0))
        else:
            behavioral_score = self._heuristic_behavior_score(event_rows)

        decoy_score = 0.0
        if self.models.decoy_model is not None and len(req.trap_events) > 0:
            trap_vectors = []
            for trap in req.trap_events:
                trap_vectors.append(
                    [
                        float(trap.get("access_freq", 0.0)),
                        float(trap.get("rename_burst", 0.0)),
                        float(trap.get("entropy_jump", 0.0)),
                        float(trap.get("unknown_process_touch", 0.0)),
                    ]
                )
            arr = np.array(trap_vectors, dtype=np.float32)
            probs = self.models.decoy_model.predict_proba(arr)
            raw_prob = float(np.max(probs[:, 1]))
            threshold = float(getattr(self.models.decoy_model, "decision_threshold", 0.5))
            decoy_score = float(np.clip((raw_prob - threshold) / max(1e-6, (1.0 - threshold)), 0.0, 1.0))
        else:
            decoy_score = self._heuristic_decoy_score(len(req.trap_events))

        behavioral_weight = max(0.0, float(settings.behavioral_weight))
        decoy_weight = max(0.0, float(settings.decoy_weight))
        total_weight = behavioral_weight + decoy_weight
        if total_weight <= 0.0:
            behavioral_weight, decoy_weight, total_weight = 0.65, 0.35, 1.0
        risk_score = float(
            np.clip(
                ((behavioral_score * behavioral_weight) + (decoy_score * decoy_weight)) / total_weight,
                0.0,
                1.0,
            )
        )
        reasons = []
        if behavioral_score > 0.65:
            reasons.append("Behavioral sequence resembles ransomware encryption pattern")
        if decoy_score > 0.5:
            reasons.append("Decoy trap interaction indicates unauthorized bulk file activity")
        if not reasons:
            reasons.append("No critical ransomware indicators above threshold")

        severity = "normal"
        if risk_score >= max(0.90, settings.alert_threshold + 0.12):
            severity = "critical"
        elif risk_score >= max(0.65, settings.alert_threshold - 0.05):
            severity = "warning"

        return DetectionResult(
            agent_id=req.agent_id,
            host=req.host,
            behavioral_score=behavioral_score,
            decoy_score=decoy_score,
            risk_score=risk_score,
            severity=severity,
            is_ransomware=risk_score >= settings.alert_threshold,
            reasons=reasons,
            suspected_processes=suspected_processes,
            timestamp=datetime.now(timezone.utc),
        )
