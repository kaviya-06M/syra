"""Quick targeted LLM test with unbuffered output."""
import sys, os
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== OFFLINE TESTS ===")

from backend.llm.conversation_memory import ConversationMemory
from backend.llm.response_formatter import ResponseFormatter

mem = ConversationMemory(max_turns=5, system_prompt="You are SYRA.")
mem.add_user_message("What is wrong?")
mem.add_assistant_message("High memory detected.")
print(f"[PASS] ConversationMemory: turns={mem.turn_count}")

fmt = ResponseFormatter()
d = fmt.format_diagnosis("High memory detected.", {"root_cause": "memory_leak", "confidence": 0.85})
print(f"[PASS] ResponseFormatter: type={d['type']}, severity={d['severity']}")

print()
print("=== LIVE API TEST 1: Diagnosis Explanation ===")

from backend.llm.provider import LLMProvider
from backend.llm.explanation import ExplanationEngine

provider = LLMProvider()
print(f"Provider: model={provider.model}")

engine = ExplanationEngine(provider=provider)

diagnosis = {
    "root_cause": "system_slowdown",
    "confidence": 0.826,
    "evidence": ["high_memory_usage", "runaway_process"],
}
anomaly = {
    "anomaly_score": 0.87,
    "threshold": 0.30,
    "contributing_features": [
        {"feature": "memory_percent", "contribution_percent": 45.2},
        {"feature": "cpu_percent", "contribution_percent": 12.5},
    ],
}

print("Calling Llama 3.1 70B...")
text = engine.explain_diagnosis(diagnosis, anomaly)
print()
print("SYRA says:")
print(text)
print()
print(f"[PASS] Diagnosis: {len(text)} chars")

print()
print("=== LIVE API TEST 2: Post-Remediation Report ===")
print("Calling Llama 3.1 70B...")

action_result = {"action": "kill_top_process", "root_cause": "system_slowdown"}
verification = {"resolved": True, "still_critical": False}
before = {"cpu": {"cpu_percent": 92}, "memory": {"memory_percent": 98}, "disk": {"disk_percent": 30}}
after = {"cpu": {"cpu_percent": 35}, "memory": {"memory_percent": 61}, "disk": {"disk_percent": 30}}

text2 = engine.explain_remediation(action_result, verification, before, after)
print()
print("SYRA says:")
print(text2)
print()
print(f"[PASS] Remediation report: {len(text2)} chars")

print()
print("=== LIVE API TEST 3: Chat ===")
from backend.llm.memory import SyraChatEngine

chat = SyraChatEngine(provider=provider)
print("Calling Llama 3.1 70B...")
resp = chat.chat("Is my computer healthy?", system_state={
    "cpu": {"cpu_percent": 25},
    "memory": {"memory_percent": 55},
    "disk": {"disk_percent": 30},
    "processes": {"top_processes": [{"name": "explorer.exe", "cpu": 2, "memory": 5}]},
})
print()
print("SYRA says:")
print(resp["message"])
print()
print(f"[PASS] Chat: {len(resp['message'])} chars")

print()
print("=== ALL LLM TESTS PASSED ===")
