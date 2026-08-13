"""Persistence helpers for the feedback-driven root-cause learning loop."""

import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from .models import Incident, IncidentFeedback


def create_incident(
    db: Session,
    *,
    event_data: dict[str, Any],
    anomaly_info: dict[str, Any] | None,
    diagnosis: dict[str, Any],
) -> Incident:
    incident = Incident(
        id=str(uuid.uuid4()),
        event_data=json.dumps(event_data, default=str),
        anomaly_info=json.dumps(anomaly_info or {}, default=str),
        matched_rules=json.dumps(diagnosis.get("matched_rules", []), default=str),
        evidence=json.dumps(diagnosis.get("evidence", []), default=str),
        rule_root_cause=diagnosis.get("rule_root_cause", diagnosis.get("root_cause")),
        rule_confidence=float(diagnosis.get("rule_confidence", diagnosis.get("confidence", 0.0))),
        ml_root_cause=diagnosis.get("ml_root_cause"),
        ml_confidence=diagnosis.get("ml_confidence"),
        final_root_cause=diagnosis.get("root_cause"),
        final_confidence=float(diagnosis.get("confidence", 0.0)),
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def get_incident(db: Session, incident_id: str) -> Incident | None:
    return db.get(Incident, incident_id)


def list_incidents(db: Session, limit: int = 50) -> list[Incident]:
    return db.query(Incident).order_by(Incident.created_at.desc()).limit(limit).all()


def save_feedback(
    db: Session,
    *,
    incident_id: str,
    feedback: str,
    verified_root_cause: str | None,
    notes: str | None,
    remediation_verified: bool | None,
) -> IncidentFeedback:
    record = db.query(IncidentFeedback).filter_by(incident_id=incident_id).one_or_none()
    if record is None:
        record = IncidentFeedback(incident_id=incident_id, feedback=feedback)
        db.add(record)

    record.feedback = feedback
    record.verified_root_cause = verified_root_cause
    record.notes = notes
    record.remediation_verified = remediation_verified
    db.commit()
    db.refresh(record)

    incident = get_incident(db, incident_id)
    if incident is not None and remediation_verified is not None:
        incident.verification_resolved = remediation_verified
        db.commit()
    return record


def update_remediation(db: Session, incident_id: str, action: str | None, resolved: bool | None = None) -> None:
    incident = get_incident(db, incident_id)
    if incident is None:
        return
    if action is not None:
        incident.remediation_action = action
    if resolved is not None:
        incident.verification_resolved = resolved
    db.commit()


def verified_incidents(db: Session) -> list[tuple[Incident, IncidentFeedback]]:
    """Return only labels safe to use for supervised training."""
    return (
        db.query(Incident, IncidentFeedback)
        .join(IncidentFeedback, Incident.id == IncidentFeedback.incident_id)
        .filter(IncidentFeedback.feedback.in_(("confirmed", "corrected")))
        .filter(IncidentFeedback.verified_root_cause.isnot(None))
        .filter(IncidentFeedback.remediation_verified.is_(True))
        .order_by(Incident.created_at.asc())
        .all()
    )
