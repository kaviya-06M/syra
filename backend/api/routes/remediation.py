"""
/remediation routes - implements the 'Ask for permission -> Execute
Action -> Verify' branch of the SYRA pipeline. The frontend calls
/propose after a diagnosis, waits for the user's Yes/No, calls
/approve, then /execute, then /verify.
"""

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

"""
/remediation routes - implements the 'Ask for permission -> Execute
Action -> Verify' branch of the SYRA pipeline. The frontend calls
/propose after a diagnosis, waits for the user's Yes/No, calls
/approve, then /execute, then /verify.
"""

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from remediation.executor import RemediationExecutor
from remediation.verifier import RemediationVerifier
from remediation.rollback import RollbackManager
from api.routes import diagnosis as diagnosis_module
from api.routes.metrics import _metrics_history
from database.database import SessionLocal
from database.incident_repository import get_incident, update_remediation, create_incident
from api.routes.history import _incident_log
from datetime import datetime

router = APIRouter(tags=["remediation"])

_executor = RemediationExecutor()
_verifier = RemediationVerifier()
_rollback_manager = RollbackManager()

# action_id -> before_snapshot, kept so /verify can compare before/after
_before_snapshots = {}


class ProposeRequest(BaseModel):
    root_cause: str | None = None
    incident_id: str | None = None
    service_name: str | None = None
    action: str | None = None


class ApproveRequest(BaseModel):
    action_id: str
    approved: bool


class ExecuteRequest(BaseModel):
    action_id: str


@router.post("/propose")
def propose(payload: ProposeRequest):
    """
    Step: 'User: Can you fix it? -> Ask for permission'. Resolves the fix
    for the given root cause (or the latest diagnosis's root cause) and
    returns a prompt to show/speak to the user.
    """
    latest = diagnosis_module._latest_diagnosis
    root_cause = payload.root_cause
    if root_cause is None:
        if latest is None or not latest.get("root_cause"):
            raise HTTPException(status_code=400, detail="No root cause available")
        root_cause = latest["root_cause"]

    incident_id = payload.incident_id or (latest or {}).get("incident_id")
    if not incident_id:
        db = SessionLocal()
        try:
            inc = create_incident(
                db,
                event_data=_metrics_history[-1] if _metrics_history else {},
                anomaly_info={"anomaly_score": (latest or {}).get("anomaly_score", 0.5)},
                diagnosis=latest or {"root_cause": root_cause, "confidence": 0.8},
            )
            incident_id = inc.id
            if latest:
                latest["incident_id"] = incident_id
        except Exception as e:
            print(f"[Remediation] Auto incident create error: {e}")
        finally:
            db.close()

    if not _metrics_history:
        raise HTTPException(status_code=400, detail="No current metrics available to select a remediation target")

    action_id = str(uuid.uuid4())
    result = _executor.propose_action(
        action_id,
        root_cause,
        snapshot=_metrics_history[-1],
        incident_id=incident_id,
        service_name=payload.service_name,
        selected_action=payload.action,
    )

    if not result.get("action_id"):
        raise HTTPException(status_code=400, detail=result.get("message"))

    _before_snapshots[action_id] = _metrics_history[-1]
    result["incident_id"] = incident_id

    return result


@router.post("/approve")
def approve(payload: ApproveRequest):
    """Step: Yes/No branch. Records the user's decision."""
    result = _executor.permissions.respond(payload.action_id, payload.approved)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result


@router.post("/execute")
def execute(payload: ExecuteRequest):
    """Execute only the exact action and target saved at approval time."""
    if not _executor.permissions.is_approved(payload.action_id):
        raise HTTPException(status_code=403, detail="Action not approved by user")

    result = _executor.execute(payload.action_id)
    # A remediation method can safely refuse an action (for example, a PID
    # exited or Windows denied a priority change). Do not report that as an
    # executed fix to the UI.
    if not result.get("success"):
        raise HTTPException(status_code=409, detail=result.get("message", "Remediation action could not be completed"))

    incident_id = result.get("incident_id")
    db = SessionLocal()
    try:
        if incident_id:
            update_remediation(db, incident_id, result.get("action"))
        else:
            inc = create_incident(
                db,
                event_data=_before_snapshots.get(payload.action_id, _metrics_history[-1] if _metrics_history else {}),
                anomaly_info={"anomaly_score": 0.5},
                diagnosis={"root_cause": result.get("root_cause", "system_slowdown"), "confidence": 0.8},
            )
            update_remediation(db, inc.id, result.get("action"))
            incident_id = inc.id
            result["incident_id"] = incident_id
    except Exception as e:
        print(f"[Remediation] execute DB update error: {e}")
    finally:
        db.close()

    # Append to in-memory history log for instant live sync
    _incident_log.append({
        "id": len(_incident_log) + 1,
        "timestamp": datetime.now().isoformat(),
        "root_cause": result.get("root_cause", "system_slowdown"),
        "action_taken": result.get("action"),
        "target": result.get("target"),
        "message": result.get("message"),
        "success": True,
        "resolved": None,
        "incident_id": incident_id,
    })

    return result


@router.post("/verify/{action_id}")
def verify(action_id: str):
    """Step: 'Verify whether the issue is resolved'."""
    before = _before_snapshots.get(action_id)
    if before is None:
        raise HTTPException(status_code=400, detail="No before-snapshot recorded for this action")

    if not _metrics_history:
        raise HTTPException(status_code=400, detail="No current metrics available")

    after = _metrics_history[-1]
    last_action = _executor.get_action(action_id)
    if last_action is None:
        raise HTTPException(status_code=404, detail="No executed action found for this action_id")

    verification = _verifier.verify(before, after, root_cause=last_action.get("root_cause"))
    incident_id = last_action.get("incident_id")
    verification["incident_id"] = incident_id

    if not verification["resolved"]:
        verification["rollback"] = _rollback_manager.rollback(last_action)

    if incident_id:
        db = SessionLocal()
        try:
            update_remediation(db, incident_id, last_action.get("action"), verification["resolved"])
        finally:
            db.close()
        verification["feedback_endpoint"] = f"/api/incidents/{incident_id}/feedback"
        verification["next_step"] = "Ask the user to confirm or correct the root cause for future model training."

    # A verified remediation closes the active diagnosis so future proposals
    # are not generated from an incident that has already been resolved.
    if verification["resolved"]:
        diagnosis_module._latest_diagnosis = None

    # Update in-memory history log
    for item in reversed(_incident_log):
        if item.get("incident_id") == incident_id or item.get("action_taken") == last_action.get("action"):
            item["resolved"] = verification.get("resolved")
            break

    return verification
