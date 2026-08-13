"""Incident review and feedback APIs for root-cause model training."""

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import get_db
from database.incident_repository import get_incident, list_incidents, save_feedback

router = APIRouter(tags=["incidents"])


class FeedbackRequest(BaseModel):
    feedback: str = Field(pattern="^(confirmed|corrected|unknown)$")
    verified_root_cause: str | None = None
    remediation_verified: bool | None = None
    notes: str | None = Field(default=None, max_length=2000)


def _incident_response(incident):
    return {
        "incident_id": incident.id,
        "created_at": incident.created_at.isoformat(),
        "event_data": json.loads(incident.event_data),
        "anomaly_info": json.loads(incident.anomaly_info),
        "matched_rules": json.loads(incident.matched_rules),
        "evidence": json.loads(incident.evidence),
        "rule_prediction": {
            "root_cause": incident.rule_root_cause,
            "confidence": incident.rule_confidence,
        },
        "ml_prediction": {
            "root_cause": incident.ml_root_cause,
            "confidence": incident.ml_confidence,
        },
        "final_prediction": {
            "root_cause": incident.final_root_cause,
            "confidence": incident.final_confidence,
        },
        "remediation_action": incident.remediation_action,
        "verification_resolved": incident.verification_resolved,
    }


@router.get("")
def get_incidents(limit: int = 50, db: Session = Depends(get_db)):
    return [_incident_response(item) for item in list_incidents(db, max(1, min(limit, 200)))]


@router.get("/{incident_id}")
def get_incident_by_id(incident_id: str, db: Session = Depends(get_db)):
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _incident_response(incident)


@router.post("/{incident_id}/feedback")
def record_feedback(incident_id: str, payload: FeedbackRequest, db: Session = Depends(get_db)):
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    if payload.feedback in {"confirmed", "corrected"} and not payload.verified_root_cause:
        raise HTTPException(
            status_code=422,
            detail="verified_root_cause is required for confirmed or corrected feedback",
        )

    feedback = save_feedback(
        db,
        incident_id=incident_id,
        feedback=payload.feedback,
        verified_root_cause=payload.verified_root_cause,
        notes=payload.notes,
        remediation_verified=payload.remediation_verified,
    )
    return {
        "incident_id": incident_id,
        "feedback": feedback.feedback,
        "verified_root_cause": feedback.verified_root_cause,
        "remediation_verified": feedback.remediation_verified,
        "eligible_for_training": bool(
            feedback.feedback in {"confirmed", "corrected"}
            and feedback.verified_root_cause
            and feedback.remediation_verified
        ),
    }
