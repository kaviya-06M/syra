"""
/diagnosis routes - triggers the Root Cause Reasoning Engine (Steps 6-8 of
the SYRA pipeline: Context Correlation -> Root Cause Reasoning ->
Recommendation) and exposes the latest diagnosis so the frontend and the
LLM chat route can both read it.
"""

import json
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from reasoning.root_cause_engine import RootCauseEngine
from api.routes.metrics import _metrics_history
from database.database import SessionLocal
from database.incident_repository import create_incident

router = APIRouter(tags=["diagnosis"])

_engine = RootCauseEngine()
_latest_diagnosis = None


class AnomalyInfo(BaseModel):
    score: float
    affected_metric: str | None = None


class DiagnosisRequest(BaseModel):
    event_data: dict | None = None
    anomaly_info: AnomalyInfo | None = None


@router.post("/analyze")
def analyze(payload: DiagnosisRequest):
    """
    Runs the Root Cause Reasoning Engine against a given event snapshot
    (or the latest collected metrics if none is provided) and stores the
    result as the 'latest diagnosis' for other routes to read.
    """
    global _latest_diagnosis

    event_data = payload.event_data
    if event_data is None:
        if not _metrics_history:
            raise HTTPException(status_code=400, detail="No metrics available to analyze")
        event_data = _metrics_history[-1]

    anomaly_info = payload.anomaly_info.dict() if payload.anomaly_info else None

    result = _engine.diagnose(event_data, anomaly_info=anomaly_info)

    # The incident graph (networkx.DiGraph) isn't JSON serializable as-is,
    # so we drop it from the API response and keep the rest.
    serializable_result = {k: v for k, v in result.items() if k != "graph"}
    serializable_result["timestamp"] = datetime.now().isoformat()

    # Capture the complete diagnosis now; it becomes ML training data only
    # after the user supplies a verified feedback label.
    if serializable_result.get("root_cause"):
        db = SessionLocal()
        try:
            incident = create_incident(
                db,
                event_data=event_data,
                anomaly_info=anomaly_info,
                diagnosis=serializable_result,
            )
            serializable_result["incident_id"] = incident.id
        finally:
            db.close()

    _latest_diagnosis = serializable_result
    print(
        "[RootCauseEngine] Diagnosis result:\n"
        f"{json.dumps(serializable_result, indent=2, default=str)}",
        flush=True,
    )
    return serializable_result


@router.get("/latest")
def get_latest_diagnosis():
    """Returns the most recent diagnosis, or a message if none exists yet."""
    if _latest_diagnosis is None:
        return {"message": "No diagnosis has been run yet"}
    return _latest_diagnosis
