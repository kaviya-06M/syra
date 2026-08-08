"""
/chat routes - the 'User: Why is my laptop slow?' step. Sends the latest
root cause diagnosis + evidence into the LLM and returns SYRA's spoken/
written explanation.

NOTE: llm/ is not implemented yet in this codebase. The import below is
wrapped so this route (and the whole API) still boots today; once
llm.explanation.ExplanationEngine exists, real answers replace the
fallback text automatically - no other route needs to change.
"""

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.routes import diagnosis as diagnosis_module
from api.routes.metrics import _metrics_history
from reasoning.root_cause_engine import RootCauseEngine

router = APIRouter(tags=["chat"])

_session_history: dict[str, list[dict]] = {}
_diagnosis_engine = RootCauseEngine()

try:
    from llm.explanation import ExplanationEngine
    _explanation_engine = ExplanationEngine()
    _LLM_READY = True
    _LLM_ERROR = None
except Exception as e:
    _explanation_engine = None
    _LLM_READY = False
    _LLM_ERROR = str(e)


class ChatMessage(BaseModel):
    session_id: str | None = None
    message: str


def _build_fallback_reply(diagnosis_context: dict | None) -> str:
    """Returns a deterministic root-cause-first reply when LLM is unavailable."""
    if not diagnosis_context:
        return "I do not have a diagnosis yet, so I cannot state a root cause. Please run diagnosis first."

    root_cause = diagnosis_context.get("root_cause", "unknown")
    confidence = diagnosis_context.get("confidence")
    evidence = diagnosis_context.get("evidence") or []

    lines = [f"Root cause: {root_cause}."]
    if confidence is not None:
        lines.append(f"Confidence: {round(float(confidence) * 100, 1)}%.")
    if evidence:
        lines.append(f"Evidence: {', '.join(str(e) for e in evidence[:3])}.")
    lines.append("I can proceed with a remediation proposal if you want.")
    return " ".join(lines)


def _get_diagnosis_context() -> dict | None:
    """Return the latest diagnosis, or derive one from the most recent metrics."""
    latest = diagnosis_module._latest_diagnosis
    if latest and latest.get("root_cause"):
        return {
            "root_cause": latest["root_cause"],
            "confidence": latest.get("confidence"),
            "evidence": latest.get("evidence", []),
        }

    if not _metrics_history:
        return None

    result = _diagnosis_engine.diagnose(_metrics_history[-1])
    if not result.get("root_cause"):
        return None

    diagnosis_module._latest_diagnosis = {
        "root_cause": result["root_cause"],
        "confidence": result.get("confidence", 0.0),
        "evidence": result.get("evidence", []),
        "path": result.get("path", []),
        "all_candidates": result.get("all_candidates", {}),
        "matched_rules": result.get("matched_rules", []),
    }
    return {
        "root_cause": result["root_cause"],
        "confidence": result.get("confidence"),
        "evidence": result.get("evidence", []),
    }


def _ensure_root_cause_first(reply: str, diagnosis_context: dict | None) -> str:
    """Guarantee the response starts with the root cause when one is known."""
    if not diagnosis_context or not diagnosis_context.get("root_cause"):
        return reply

    root_cause = diagnosis_context.get("root_cause", "unknown")
    confidence = diagnosis_context.get("confidence")
    evidence = diagnosis_context.get("evidence") or []

    prefix = [f"Root cause: {root_cause}."]
    if confidence is not None:
        try:
            prefix.append(f"Confidence: {round(float(confidence) * 100, 1)}%.")
        except (TypeError, ValueError):
            pass
    if evidence:
        prefix.append(f"Evidence: {', '.join(str(item) for item in evidence[:3])}.")

    prefix_text = " ".join(prefix)
    if reply.lstrip().startswith("Root cause:"):
        return reply
    return f"{prefix_text} {reply}".strip()


@router.post("/message")
def send_message(payload: ChatMessage):
    """
    Sends a user message to SYRA. If a diagnosis exists, its root cause
    and evidence are passed to the LLM as context so questions like
    'Why is my laptop slow?' get a grounded answer instead of a guess.
    """
    session_id = payload.session_id or str(uuid.uuid4())
    history = _session_history.get(session_id, [])

    diagnosis_context = _get_diagnosis_context()

    if _LLM_READY:
        try:
            reply = _explanation_engine.explain(
                user_message=payload.message,
                diagnosis=diagnosis_context,
                history=history,
            )
        except Exception as exc:
            reply = _build_fallback_reply(diagnosis_context)
            print(f"[LLM] Falling back after error: {exc.__class__.__name__}: {exc}")
    else:
        reply = _build_fallback_reply(diagnosis_context)

    reply = _ensure_root_cause_first(reply, diagnosis_context)

    updated_history = history + [
        {"role": "user", "content": payload.message},
        {"role": "assistant", "content": reply},
    ]
    _session_history[session_id] = updated_history[-20:]

    return {
        "session_id": session_id,
        "reply": reply,
        "used_diagnosis": diagnosis_context is not None,
        "llm_ready": _LLM_READY,
        "llm_error": _LLM_ERROR,
    }


@router.get("/history/{session_id}")
def get_chat_history(session_id: str):
    return {"session_id": session_id, "history": _session_history.get(session_id, [])}
