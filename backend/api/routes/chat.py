"""
/chat routes - the 'User: Why is my laptop slow?' step. Sends the latest
root cause diagnosis + evidence into the LLM and returns SYRA's spoken/
written explanation.
"""

import uuid
import re
from copy import deepcopy

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.routes import diagnosis as diagnosis_module
from api.routes.metrics import _metrics_history
from reasoning.root_cause_engine import RootCauseEngine
from ml.inference.inference_engine import InferenceEngine

router = APIRouter(tags=["chat"])

_session_history: dict[str, list[dict]] = {}
# An active diagnosis is deliberately pinned to a chat session.  The
# background monitor produces a new reading every few seconds; without this,
# a follow-up message could be answered using a different (and possibly
# healthy) reading than the one that triggered the conversation.
_session_diagnoses: dict[str, dict] = {}
_diagnosis_engine = RootCauseEngine()
_inference_engine = InferenceEngine()

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


def _build_fallback_reply(diagnosis_context: dict | None, user_message: str = "", metrics: dict | None = None) -> str:
    """Dynamically answers user questions accurately using live telemetry and root-cause context when cloud LLM is slow or offline."""
    user_msg_lower = (user_message or "").lower().strip()
    metrics = metrics or {}
    
    # Extract live hardware numbers (filtering protected system processes)
    cpu_pct = metrics.get("cpu", {}).get("cpu_percent", 0.0)
    mem_pct = metrics.get("memory", {}).get("memory_percent", 0.0)
    disk_pct = metrics.get("disk", {}).get("disk_percent", 0.0)
    
    from remediation.actions import RemediationActions
    top_procs = metrics.get("processes", {}).get("top_processes", [])
    user_procs = [p for p in top_procs if not RemediationActions.is_protected_process(p.get("name"))]
    top_p = user_procs[0] if user_procs else (top_procs[0] if top_procs else {})
    top_name = top_p.get("name", "active apps")
    top_mem = top_p.get("memory", 0.0)
    top_cpu = top_p.get("cpu", 0.0)

    root_cause = (diagnosis_context or {}).get("root_cause")
    evidence = (diagnosis_context or {}).get("evidence", [])
    path = (diagnosis_context or {}).get("path", [])

    # 1. User says Yes / Approve / Fix it / Proceed
    if any(w in user_msg_lower for w in ["yes", "proceed", "fix", "solve", "approve", "do it", "sure", "ok", "okay"]):
        return "Please open the Fix & Approval tab and click 'Review & Approve Fix' to execute this remediation safely."

    # 2. User asks what should I do next / what to do / recommendation
    if any(w in user_msg_lower for w in ["what should i do", "next", "what can i do", "recommend", "how to fix", "how do i fix"]):
        if root_cause:
            cause_clean = str(root_cause).replace("_", " ")
            return f"To resolve the {cause_clean}, I recommend freeing background memory or lowering {top_name}'s priority. Please approve this fix in the Fix & Approval tab."
        return "Your computer is operating normally. No remediation action is required right now."

    # 3. User asks about root cause / why PC is slow / what is wrong
    if any(w in user_msg_lower for w in ["slow", "lag", "freeze", "why", "wrong", "problem", "issue", "trouble", "root cause", "cause"]):
        if root_cause:
            cause_clean = str(root_cause).replace("_", " ")
            chain = " -> ".join(str(p).replace("_", " ") for p in path) if path else cause_clean
            return f"Diagnosed Root Cause: {cause_clean.title()} (Causal Path: {chain}). Top active app is {top_name} (CPU: {top_cpu}%, RAM: {top_mem}%). You can approve the fix in Fix & Approval."
        if mem_pct > 80:
            return f"RAM usage is elevated at {mem_pct}%, utilized by {top_name} ({top_mem}%). Freeing memory in Fix & Approval will improve performance."
        return f"System load is currently normal (CPU: {cpu_pct}%, RAM: {mem_pct}%). No active root cause detected."

    # 4. User asks about health or status (e.g. "how is pc health now")
    if any(w in user_msg_lower for w in ["health", "status", "how is", "doing", "check", "nominal", "healthy", "condition"]):
        if root_cause:
            cause_clean = str(root_cause).replace("_", " ")
            return f"PC Health Alert: {cause_clean.title()} identified (CPU: {cpu_pct}%, RAM: {mem_pct}%). I recommend applying the remediation in the Fix & Approval tab."
        return f"Your computer is healthy and running smoothly (CPU: {cpu_pct}%, RAM: {mem_pct}%, Disk: {disk_pct}%)."

    # 5. User asks about processes / apps
    if any(w in user_msg_lower for w in ["process", "task", "running", "apps", "program"]):
        top_list = [f"{p.get('name')} ({p.get('memory', 0)}% RAM)" for p in user_procs[:3]]
        return f"Top active user applications: {', '.join(top_list) if top_list else top_name}."

    # 6. User says Hello / Greeting
    if any(w in user_msg_lower for w in ["hello", "hi", "hey"]):
        return "Hello! I am SYRA, your computer health assistant. How can I help you today?"

    # 7. User says Thank you / Done
    if any(w in user_msg_lower for w in ["thank", "thanks", "done", "great"]):
        return "You're welcome! I'll continue monitoring your system silently in the background."

    # Default friendly contextual response
    if root_cause:
        cause = str(root_cause).replace("_", " ")
        return f"Current diagnosed issue: {cause} (CPU: {cpu_pct}%, RAM: {mem_pct}%). Head to Fix & Approval to review the proposed fix."
    
    return f"System is currently running at {cpu_pct}% CPU and {mem_pct}% RAM. Feel free to ask any question about your computer health."


def _direct_reply(user_message: str, metrics: dict | None) -> str | None:
    """Answer strictly factual single-metric telemetry lookups from live facts.

    Open-ended questions (e.g. health status, root cause, remediation, fix recommendations)
    are left for the LLM explanation engine to answer contextually.
    """
    text = re.sub(r"\s+", " ", (user_message or "").casefold()).strip()
    metrics = metrics or {}
    cpu = metrics.get("cpu", {}).get("cpu_percent")
    memory = metrics.get("memory", {}).get("memory_percent")
    disk = metrics.get("disk", {}).get("disk_percent")
    network = metrics.get("network", {})
    processes = metrics.get("processes", {}).get("top_processes", [])

    def number(value, default=0.0):
        try:
            return round(float(value), 1)
        except (TypeError, ValueError):
            return default

    cpu_value, memory_value, disk_value = number(cpu), number(memory), number(disk)

    if re.search(r"\b(close|shut|dismiss)\b.*\b(tab|browser)\b|\b(tab|browser)\b.*\b(close|shut)\b", text):
        return "I can close one active browser tab, but I will not do it without your approval. Open Fix & Approval, choose close_browser_tab, and approve the proposed action."

    if re.search(r"^(what is|tell me|show me|check)?\s*(my\s+)?(cpu|processor)\s*(usage|use|load|percent|percentage)?\??$", text) or text in ["cpu", "cpu usage", "how much cpu"]:
        return f"Current CPU usage is {cpu_value}%."

    if re.search(r"^(what is|tell me|show me|check)?\s*(my\s+)?(memory|ram)\s*(usage|use|load|percent|percentage|pressure)?\??$", text) or text in ["ram", "memory", "ram usage", "memory usage", "how much ram"]:
        return f"Current memory usage is {memory_value}%."

    if re.search(r"^(what is|tell me|show me|check)?\s*(my\s+)?(disk|storage|drive)\s*(usage|use|space|percent|percentage|free)?\??$", text) or text in ["disk", "disk usage", "storage"]:
        return f"Current disk usage is {disk_value}%."

    if re.search(r"^(what is|tell me|show me|check)?\s*(my\s+)?(network|internet|bandwidth|traffic)\s*(usage|stats)?\??$", text) or text in ["network", "bandwidth", "traffic"]:
        sent = number(network.get("bytes_sent"))
        received = number(network.get("bytes_received"))
        return f"Network counters show {sent} MB sent and {received} MB received since monitoring started."

    return None


def _get_diagnosis_context() -> dict | None:
    """Return the latest diagnosis, or derive one from the most recent metrics."""
    latest = diagnosis_module._latest_diagnosis
    if latest and latest.get("root_cause"):
        return {
            "root_cause": latest["root_cause"],
            "confidence": latest.get("confidence"),
            "evidence": latest.get("evidence", []),
            "path": latest.get("path", []),
            "timestamp": latest.get("timestamp"),
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
        "timestamp": _metrics_history[-1].get("timestamp"),
    }
    return {
        "root_cause": result["root_cause"],
        "confidence": result.get("confidence"),
        "evidence": result.get("evidence", []),
        "path": result.get("path", []),
        "timestamp": _metrics_history[-1].get("timestamp"),
    }


@router.post("/message")
def send_message(payload: ChatMessage):
    """
    Sends a user message to SYRA. If a diagnosis exists, its root cause
    and evidence are passed to the LLM as context so questions like
    'Why is my laptop slow?' get a grounded answer instead of a guess.
    """
    session_id = payload.session_id or str(uuid.uuid4())
    history = _session_history.get(session_id, [])

    pinned_context = _session_diagnoses.get(session_id)
    diagnosis_context = pinned_context.get("diagnosis") if pinned_context else _get_diagnosis_context()

    # Use the telemetry captured with the diagnosis for the rest of this
    # conversation. Metric-only questions continue to use live telemetry when
    # the session has no active diagnosis.
    latest_metrics = pinned_context.get("metrics", {}) if pinned_context else (_metrics_history[-1] if _metrics_history else {})
    if not latest_metrics or not latest_metrics.get("cpu"):
        try:
            from agent.collector import AgentCollector
            latest_metrics = AgentCollector().collect()
        except Exception:
            pass

    if diagnosis_context and diagnosis_context.get("root_cause") and not pinned_context:
        _session_diagnoses[session_id] = {
            "diagnosis": deepcopy(diagnosis_context),
            "metrics": deepcopy(latest_metrics),
        }
    ml_analysis = {}
    try:
        if latest_metrics:
            ml_analysis = _inference_engine.process_snapshot(latest_metrics)
    except Exception as exc:
        print(f"[ML] Inference unavailable: {exc.__class__.__name__}: {exc}")

    direct_reply = _direct_reply(payload.message, latest_metrics)
    if direct_reply is not None:
        reply = direct_reply
    elif _LLM_READY:
        try:
            reply = _explanation_engine.explain(
                user_message=payload.message,
                diagnosis=diagnosis_context,
                history=history,
                ml_analysis=ml_analysis,
                metrics=latest_metrics,
            )
        except Exception as exc:
            reply = _build_fallback_reply(diagnosis_context, user_message=payload.message, metrics=latest_metrics)
            print(f"[LLM] Falling back after error: {exc.__class__.__name__}: {exc}")
    else:
        reply = _build_fallback_reply(diagnosis_context, user_message=payload.message, metrics=latest_metrics)

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
        "ml_analysis": ml_analysis,
    }


@router.get("/history/{session_id}")
def get_chat_history(session_id: str):
    return {"session_id": session_id, "history": _session_history.get(session_id, [])}
