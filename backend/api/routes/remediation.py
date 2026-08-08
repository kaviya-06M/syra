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

router = APIRouter(tags=["remediation"])

_executor = RemediationExecutor()
_verifier = RemediationVerifier()
_rollback_manager = RollbackManager()

# action_id -> before_snapshot, kept so /verify can compare before/after
_before_snapshots = {}


class ProposeRequest(BaseModel):
    root_cause: str | None = None


class ApproveRequest(BaseModel):
    action_id: str
    approved: bool


class ExecuteRequest(BaseModel):
    action_id: str
    root_cause: str


@router.post("/propose")
def propose(payload: ProposeRequest):
    """
    Step: 'User: Can you fix it? -> Ask for permission'. Resolves the fix
    for the given root cause (or the latest diagnosis's root cause) and
    returns a prompt to show/speak to the user.
    """
    root_cause = payload.root_cause
    if root_cause is None:
        latest = diagnosis_module._latest_diagnosis
        if latest is None or not latest.get("root_cause"):
            raise HTTPException(status_code=400, detail="No root cause available")
        root_cause = latest["root_cause"]

    action_id = str(uuid.uuid4())
    result = _executor.propose_action(action_id, root_cause)

    if not result.get("action_id"):
        raise HTTPException(status_code=400, detail=result.get("message"))

    if _metrics_history:
        _before_snapshots[action_id] = _metrics_history[-1]

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
    """Step: 'Execute Action'. Only runs if the user already approved it."""
    result = _executor.execute(payload.action_id, payload.root_cause)
    if not result.get("success"):
        raise HTTPException(status_code=403, detail=result.get("message"))
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
    last_action = _executor.get_last_action()

    verification = _verifier.verify(before, after, root_cause=last_action.get("root_cause") if last_action else None)

    if not verification["resolved"] and last_action:
        verification["rollback"] = _rollback_manager.rollback(last_action)

    return verification
