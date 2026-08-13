"""
SYRA Full Pipeline & LLM Validation Test
=========================================
Tests:
1. LLM Output on Health Queries ('how is pc health now', 'is my computer healthy')
2. LLM Output on Root Cause & Remediation ('what is the root cause', 'how can you fix it')
3. Fallback Reply correctness when LLM is offline
4. Remediation Workflow: Propose -> Approve -> Execute -> Verify
5. Chat API Endpoint End-to-End
"""

import sys
import os

# Set sys.path so backend imports work
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_root = os.path.dirname(os.path.abspath(__file__))
for p in (workspace_root, backend_root):
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.llm.provider import LLMProvider
from backend.llm.explanation import ExplanationEngine
from backend.remediation.executor import RemediationExecutor
from backend.remediation.verifier import RemediationVerifier
from backend.reasoning.root_cause_engine import RootCauseEngine
from backend.api.routes.chat import send_message, ChatMessage, _build_fallback_reply
from backend.api.routes.metrics import record_snapshot

print("=" * 70)
print("1. TESTING LLM PROVIDER & EXPLANATION ENGINE")
print("=" * 70)

provider = LLMProvider()
engine = ExplanationEngine(provider=provider)

# Scenario A: Healthy system
healthy_metrics = {
    "cpu": {"cpu_percent": 15.2},
    "memory": {"memory_percent": 42.0},
    "disk": {"disk_percent": 50.0},
    "processes": {"top_processes": [{"name": "system", "cpu": 1.0, "memory": 2.0}]},
}

print("\n[Test 1A] Query: 'how is pc health now' (Healthy state)")
ans_healthy = engine.explain("how is pc health now", diagnosis=None, metrics=healthy_metrics)
print("SYRA Response:")
print(ans_healthy)
assert len(ans_healthy) > 10, "Response is too short"
print("-> SUCCESS")

# Scenario B: Unhealthy system with diagnosed root cause (memory leak)
anomaly_diag = {
    "root_cause": "memory_leak",
    "confidence": 0.89,
    "evidence": ["high_memory_usage", "runaway_process"],
}
anomaly_metrics = {
    "cpu": {"cpu_percent": 35.0},
    "memory": {"memory_percent": 91.5},
    "disk": {"disk_percent": 50.0},
    "processes": {"top_processes": [{"name": "chrome.exe", "pid": 1234, "cpu": 5.0, "memory": 45.0}]},
}

print("\n[Test 1B] Query: 'how is pc health now' (Memory leak state)")
ans_leak = engine.explain("how is pc health now", diagnosis=anomaly_diag, metrics=anomaly_metrics)
print("SYRA Response:")
print(ans_leak)
assert len(ans_leak) > 10, "Response is too short"
print("-> SUCCESS")

print("\n[Test 1C] Query: 'what is the root cause and remediation?'")
ans_cause = engine.explain("what is the root cause and remediation?", diagnosis=anomaly_diag, metrics=anomaly_metrics)
print("SYRA Response:")
print(ans_cause)
assert len(ans_cause) > 10, "Response is too short"
print("-> SUCCESS")

print("\n" + "=" * 70)
print("2. TESTING FALLBACK REPLIES (WHEN OFFLINE)")
print("=" * 70)

fallback_healthy = _build_fallback_reply(None, user_message="how is pc health now", metrics=healthy_metrics)
print("\n[Fallback Healthy] 'how is pc health now':")
print(fallback_healthy)
assert "good" in fallback_healthy.lower() or "smooth" in fallback_healthy.lower() or "15.2" in fallback_healthy

fallback_leak = _build_fallback_reply(anomaly_diag, user_message="how is pc health now", metrics=anomaly_metrics)
print("\n[Fallback Issue] 'how is pc health now':")
print(fallback_leak)
assert "memory leak" in fallback_leak.lower() or "attention" in fallback_leak.lower()

fallback_fix = _build_fallback_reply(anomaly_diag, user_message="what should i do to fix it?", metrics=anomaly_metrics)
print("\n[Fallback Fix] 'what should i do to fix it?':")
print(fallback_fix)
assert "remediation" in fallback_fix.lower() or "memory" in fallback_fix.lower()
print("-> SUCCESS")

print("\n" + "=" * 70)
print("3. TESTING REMEDIATION WORKFLOW")
print("=" * 70)

executor = RemediationExecutor()
verifier = RemediationVerifier()

# Step 1: Propose
proposal = executor.propose_action(
    action_id="test-action-101",
    root_cause="memory_leak",
    snapshot=anomaly_metrics,
)
print("\n[Remediation Propose]")
print(f"Action ID: {proposal.get('action_id')}")
print(f"Action Name: {proposal.get('action_name')}")
print(f"Description: {proposal.get('description')}")
print(f"Alternatives: {[a['action'] for a in proposal.get('alternatives', [])]}")
assert proposal.get("action_id") == "test-action-101"

# Step 2: Approve
app_res = executor.permissions.respond("test-action-101", approved=True)
print("\n[Remediation Approve]")
print(f"Approved: {app_res.get('status')}")
assert app_res.get("success") is True

# Step 3: Execute safe action (e.g. free_memory)
exec_res = executor.execute("test-action-101")
print("\n[Remediation Execute]")
print(f"Success: {exec_res.get('success')}")
print(f"Action: {exec_res.get('action')}")
print(f"Message: {exec_res.get('message')}")
assert exec_res.get("success") is True

# Step 4: Verify
after_metrics = {
    "cpu": {"cpu_percent": 18.0},
    "memory": {"memory_percent": 55.0},
    "disk": {"disk_percent": 50.0},
}
ver_res = verifier.verify(anomaly_metrics, after_metrics, root_cause="memory_leak")
print("\n[Remediation Verify]")
print(f"Resolved: {ver_res.get('resolved')}")
print(f"Message: {ver_res.get('message')}")
assert ver_res.get("resolved") is True
print("-> SUCCESS")

print("\n" + "=" * 70)
print("4. TESTING CHAT ROUTE /MESSAGE ENDPOINT")
print("=" * 70)

# Record snapshot so chat route has live telemetry
record_snapshot(anomaly_metrics)

chat_payload = ChatMessage(message="how is pc health now")
response = send_message(chat_payload)
print("\n[Chat API Response]")
print(f"Session ID: {response.get('session_id')}")
print(f"LLM Ready: {response.get('llm_ready')}")
print(f"Reply: {response.get('reply')}")
assert len(response.get("reply", "")) > 10
print("-> SUCCESS")

print("\n" + "=" * 70)
print("ALL VALIDATION TESTS COMPLETED SUCCESSFULLY!")
print("=" * 70)
