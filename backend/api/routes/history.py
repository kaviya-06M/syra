"""
/history routes - lets the frontend list past anomalies/diagnoses and
the remediation actions taken for them, so the user can look back at
what SYRA has already caught and fixed.

NOTE: database/ is not implemented yet in this codebase, so history is
kept in-memory here for now. Swap _incident_log for database.crud calls
once database/models.py and database/crud.py are implemented - the
route signatures below won't need to change.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["history"])

_incident_log = []


class IncidentRecord(BaseModel):
    root_cause: str
    confidence: float
    evidence: list = []
    action_taken: str | None = None
    resolved: bool | None = None


@router.post("/incidents")
def log_incident(payload: IncidentRecord):
    """
    Called internally (e.g. after /remediation/verify) to persist a
    completed diagnosis + remediation cycle into the history log.
    """
    record = payload.dict()
    record["id"] = len(_incident_log) + 1
    record["timestamp"] = datetime.now().isoformat()
    _incident_log.append(record)
    return record


@router.get("/incidents")
def list_incidents(limit: int = 20):
    """Returns the most recent incidents, most recent first."""
    limit = max(1, limit)
    return list(reversed(_incident_log))[:limit]


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: int):
    for record in _incident_log:
        if record["id"] == incident_id:
            return record
    raise HTTPException(status_code=404, detail="Incident not found")


@router.get("/stats")
def get_stats():
    """Quick summary counts for a history/dashboard page."""
    total = len(_incident_log)
    resolved = sum(1 for r in _incident_log if r.get("resolved"))
    return {
        "total_incidents": total,
        "resolved": resolved,
        "unresolved": total - resolved
    }
