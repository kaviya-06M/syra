from datetime import datetime
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database.database import SessionLocal
from database.incident_repository import (
    create_incident,
    get_incident as db_get_incident,
    list_incidents as db_list_incidents,
)
from database.models import Incident

router = APIRouter(tags=["history"])

_incident_log = []


class IncidentRecord(BaseModel):
    root_cause: str
    confidence: float = 0.8
    evidence: list = []
    action_taken: str | None = None
    resolved: bool | None = None
    target: dict | None = None
    message: str | None = None


@router.post("/incidents")
def log_incident(payload: IncidentRecord):
    """
    Persist a completed diagnosis + remediation cycle into the SQLite database and in-memory log.
    """
    record = payload.dict()
    record["id"] = len(_incident_log) + 1
    record["timestamp"] = datetime.now().isoformat()
    _incident_log.append(record)

    db = SessionLocal()
    try:
        inc = create_incident(
            db,
            event_data={"source": "manual_or_remediation_log"},
            anomaly_info={"score": 0.5},
            diagnosis={
                "root_cause": payload.root_cause,
                "confidence": payload.confidence,
                "evidence": payload.evidence,
            },
        )
        if payload.action_taken:
            inc.remediation_action = payload.action_taken
        if payload.resolved is not None:
            inc.verification_resolved = payload.resolved
        db.commit()
        record["incident_id"] = inc.id
    except Exception as e:
        print(f"[History] DB persist error: {e}")
    finally:
        db.close()

    return record


@router.get("/incidents")
def list_incidents(limit: int = 50, resolved_only: bool = True):
    """
    Returns only successfully resolved incidents from the SQLite database.
    Deduplicates repeated occurrences of the same root cause so history stays clean.
    """
    limit = max(1, limit)
    db = SessionLocal()
    try:
        db_items = db_list_incidents(db, limit=limit * 2)
        results = []
        seen_causes = set()

        for inc in db_items:
            # 1. Filter: ONLY store/display if problem was actually resolved with remediation
            is_resolved = inc.verification_resolved is True or (inc.remediation_action is not None and inc.verification_resolved is not False)
            if resolved_only and not is_resolved:
                continue

            root_cause_clean = (inc.final_root_cause or inc.rule_root_cause or "system_slowdown").strip().lower()
            action_clean = (inc.remediation_action or "").strip().lower()
            key = f"{root_cause_clean}:{action_clean}"

            # 2. De-duplicate: If the same problem occurred again, keep only the latest resolved record
            if key in seen_causes:
                continue
            seen_causes.add(key)

            try:
                ev = json.loads(inc.evidence or "[]")
            except Exception:
                ev = []

            results.append({
                "id": inc.id,
                "timestamp": inc.created_at.isoformat() if inc.created_at else datetime.now().isoformat(),
                "root_cause": inc.final_root_cause or inc.rule_root_cause or "system_slowdown",
                "confidence": inc.final_confidence or inc.rule_confidence or 0.8,
                "evidence": ev,
                "action_taken": inc.remediation_action,
                "resolved": True,
            })

            if len(results) >= limit:
                break

        if results:
            return results
    except Exception as e:
        print(f"[History] DB query error: {e}")
    finally:
        db.close()

    # Fallback to in-memory log, filtered for resolved only and deduplicated
    resolved_in_memory = []
    seen_mem = set()
    for item in reversed(_incident_log):
        if item.get("resolved") is False or not item.get("action_taken"):
            continue
        key = f"{item.get('root_cause')}:{item.get('action_taken')}"
        if key in seen_mem:
            continue
        seen_mem.add(key)
        resolved_in_memory.append(item)

    return resolved_in_memory[:limit]


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    db = SessionLocal()
    try:
        inc = db_get_incident(db, incident_id)
        if inc is not None:
            try:
                ev = json.loads(inc.evidence or "[]")
            except Exception:
                ev = []
            return {
                "id": inc.id,
                "timestamp": inc.created_at.isoformat() if inc.created_at else datetime.now().isoformat(),
                "root_cause": inc.final_root_cause or inc.rule_root_cause or "system_slowdown",
                "confidence": inc.final_confidence or inc.rule_confidence or 0.8,
                "evidence": ev,
                "action_taken": inc.remediation_action,
                "resolved": inc.verification_resolved,
            }
    finally:
        db.close()

    for record in _incident_log:
        if str(record.get("id")) == str(incident_id) or record.get("incident_id") == str(incident_id):
            return record
    raise HTTPException(status_code=404, detail="Incident not found")


@router.get("/stats")
def get_stats():
    """Quick summary counts for a history/dashboard page."""
    db = SessionLocal()
    try:
        total = db.query(Incident).count()
        resolved = db.query(Incident).filter(Incident.verification_resolved.is_(True)).count()
        if total > 0:
            return {
                "total_incidents": total,
                "resolved": resolved,
                "unresolved": total - resolved,
            }
    except Exception as e:
        print(f"[History] Stats error: {e}")
    finally:
        db.close()

    total = len(_incident_log)
    resolved = sum(1 for r in _incident_log if r.get("resolved"))
    return {
        "total_incidents": total,
        "resolved": resolved,
        "unresolved": total - resolved,
    }
