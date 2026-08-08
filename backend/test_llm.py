"""
SYRA LLM Layer Test
====================
Tests the full LLM pipeline with Llama 3.1 70B via NVIDIA NIM:
  1. Import verification
  2. ConversationMemory logic
  3. ResponseFormatter logic
  4. Live API call: Diagnosis explanation
  5. Live API call: Remediation proposal
  6. Live API call: Post-remediation report
  7. Live API call: Chat follow-up
  8. Live API call: Welcome message
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []

def log(stage, status, detail=""):
    tag = PASS if status else FAIL
    print(f"  {tag} {stage}  ->  {detail}")
    results.append((stage, status, detail))


# ============================================================================
# TEST 1: Import verification
# ============================================================================
print("\n" + "=" * 70)
print("TEST 1: Import all LLM modules")
print("=" * 70)

try:
    from backend.llm.provider import LLMProvider
    from backend.llm.prompts import SYSTEM_PROMPT, DIAGNOSIS_TEMPLATE
    from backend.llm.explanation import ExplanationEngine
    from backend.llm.conversation_memory import ConversationMemory
    from backend.llm.response_formatter import ResponseFormatter
    from backend.llm.memory import SyraChatEngine
    log("All imports", True, "6 modules loaded")
except Exception as e:
    log("Imports", False, str(e))
    import traceback; traceback.print_exc()
    sys.exit(1)


# ============================================================================
# TEST 2: ConversationMemory (offline)
# ============================================================================
print("\n" + "=" * 70)
print("TEST 2: ConversationMemory - message tracking")
print("=" * 70)

mem = ConversationMemory(max_turns=5, system_prompt="You are SYRA.")
mem.add_user_message("What's wrong?")
mem.add_assistant_message("I detected high memory usage.")
mem.add_user_message("Can you fix it?")

log("Turn count", mem.turn_count == 2, f"turns={mem.turn_count}")
log("Last user msg", mem.last_user_message == "Can you fix it?", f"msg={mem.last_user_message}")

msgs = mem.get_messages()
log("Message format", msgs[0]["role"] == "system" and len(msgs) == 4,
    f"total messages={len(msgs)}, first role={msgs[0]['role']}")

mem.set_diagnosis_context({"root_cause": "memory_leak", "confidence": 0.82})
msgs2 = mem.get_messages()
has_context = any("memory_leak" in m.get("content", "") for m in msgs2)
log("Diagnosis context injected", has_context, "context appears in messages")

mem.clear()
log("Clear memory", mem.turn_count == 0, f"turns after clear={mem.turn_count}")


# ============================================================================
# TEST 3: ResponseFormatter (offline)
# ============================================================================
print("\n" + "=" * 70)
print("TEST 3: ResponseFormatter - structure output")
print("=" * 70)

fmt = ResponseFormatter()

diag_out = fmt.format_diagnosis(
    "1. High memory detected. 2. Chrome is using too much. 3. I recommend closing tabs.",
    {"root_cause": "memory_leak", "confidence": 0.85}
)
log("Diagnosis format", diag_out["type"] == "diagnosis" and diag_out["severity"] == "critical",
    f"type={diag_out['type']}, severity={diag_out['severity']}")
log("Sections parsed", "explanation" in diag_out["sections"],
    f"sections={list(diag_out['sections'].keys())}")

prop_out = fmt.format_proposal("I can fix this by...", "kill_top_process")
log("Proposal format", prop_out["type"] == "proposal" and prop_out["action_required"],
    f"type={prop_out['type']}")

rem_out = fmt.format_remediation_result("Issue resolved!", {"resolved": True})
log("Remediation format", rem_out["severity"] == "success" and rem_out["resolved"],
    f"severity={rem_out['severity']}")

rem_fail = fmt.format_remediation_result("Issue persists.", {"resolved": False})
log("Failed remediation", rem_fail["severity"] == "warning" and not rem_fail["resolved"],
    f"severity={rem_fail['severity']}")

json_str = fmt.to_json(diag_out)
log("JSON serialization", '"type": "diagnosis"' in json_str, f"length={len(json_str)} chars")


# ============================================================================
# TEST 4: LLMProvider connection
# ============================================================================
print("\n" + "=" * 70)
print("TEST 4: LLMProvider - connect to NVIDIA NIM")
print("=" * 70)

try:
    provider = LLMProvider()
    log("Provider created", True, f"model={provider.model}, base_url={provider.base_url}")
except Exception as e:
    log("Provider creation", False, str(e))
    print("\n  Cannot continue without API key. Stopping live tests.")
    provider = None


# ============================================================================
# TEST 5: Live - Diagnosis Explanation
# ============================================================================
if provider:
    print("\n" + "=" * 70)
    print("TEST 5: LIVE - Diagnosis explanation (Llama 3.1 70B)")
    print("=" * 70)

    try:
        engine = ExplanationEngine(provider=provider)

        diagnosis = {
            "root_cause": "system_slowdown",
            "confidence": 0.826,
            "evidence": ["high_memory_usage", "runaway_process", "high_cpu_usage"],
            "path": ["anomaly", "high_memory_usage", "memory_leak", "system_slowdown"],
        }
        anomaly_report = {
            "is_anomaly": True,
            "anomaly_score": 0.87,
            "threshold": 0.30,
            "contributing_features": [
                {"feature": "memory_percent", "contribution_percent": 45.2},
                {"feature": "top_process_memory", "contribution_percent": 31.8},
                {"feature": "cpu_percent", "contribution_percent": 12.5},
            ],
        }

        print("  Calling Llama 3.1 70B...")
        explanation = engine.explain_diagnosis(diagnosis, anomaly_report)
        log("Diagnosis explanation", len(explanation) > 20, f"length={len(explanation)} chars")
        print(f"\n  SYRA says:\n  {explanation}\n")

    except Exception as e:
        log("Diagnosis explanation", False, str(e))
        import traceback; traceback.print_exc()


# ============================================================================
# TEST 6: Live - Remediation Proposal
# ============================================================================
if provider:
    print("\n" + "=" * 70)
    print("TEST 6: LIVE - Remediation proposal")
    print("=" * 70)

    try:
        proposal_text = engine.explain_proposal(
            root_cause="system_slowdown",
            action_name="kill_top_process",
            action_description="This will close the process using the most resources.",
            risk_level="medium",
        )
        log("Remediation proposal", len(proposal_text) > 20, f"length={len(proposal_text)} chars")
        print(f"\n  SYRA asks:\n  {proposal_text}\n")

    except Exception as e:
        log("Remediation proposal", False, str(e))
        import traceback; traceback.print_exc()


# ============================================================================
# TEST 7: Live - Post-Remediation Report
# ============================================================================
if provider:
    print("\n" + "=" * 70)
    print("TEST 7: LIVE - Post-remediation report (98% -> 61%)")
    print("=" * 70)

    try:
        action_result = {"action": "kill_top_process", "root_cause": "system_slowdown", "success": True}
        verification = {"resolved": True, "still_critical": False}
        before = {"cpu": {"cpu_percent": 92}, "memory": {"memory_percent": 98}, "disk": {"disk_percent": 30}}
        after = {"cpu": {"cpu_percent": 35}, "memory": {"memory_percent": 61}, "disk": {"disk_percent": 30}}

        remediation_text = engine.explain_remediation(action_result, verification, before, after)
        log("Post-remediation", len(remediation_text) > 20, f"length={len(remediation_text)} chars")
        print(f"\n  SYRA says:\n  {remediation_text}\n")

    except Exception as e:
        log("Post-remediation", False, str(e))
        import traceback; traceback.print_exc()


# ============================================================================
# TEST 8: Live - SyraChatEngine (full chat flow)
# ============================================================================
if provider:
    print("\n" + "=" * 70)
    print("TEST 8: LIVE - SyraChatEngine full chat flow")
    print("=" * 70)

    try:
        chat = SyraChatEngine(provider=provider)

        # Welcome
        print("  [Welcome]")
        welcome = chat.welcome(system_state={
            "cpu": {"cpu_percent": 25},
            "memory": {"memory_percent": 55},
            "disk": {"disk_percent": 30},
        })
        log("Welcome message", welcome["type"] == "welcome", f"severity={welcome['severity']}")
        print(f"  SYRA: {welcome['message']}\n")

        # User asks a question
        print("  [User asks: 'Is my computer healthy?']")
        response = chat.chat(
            "Is my computer healthy?",
            system_state={
                "cpu": {"cpu_percent": 25},
                "memory": {"memory_percent": 55},
                "disk": {"disk_percent": 30},
                "processes": {"top_processes": [{"name": "explorer.exe", "cpu": 2, "memory": 5}]},
            }
        )
        log("Chat response", response["type"] == "chat", f"length={len(response['message'])} chars")
        print(f"  SYRA: {response['message']}\n")

        # Memory tracking
        log("Memory tracked", chat.memory.turn_count >= 1, f"turns={chat.memory.turn_count}")

    except Exception as e:
        log("SyraChatEngine", False, str(e))
        import traceback; traceback.print_exc()


# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("LLM LAYER TEST SUMMARY")
print("=" * 70)
passed = sum(1 for _, s, _ in results if s)
failed = sum(1 for _, s, _ in results if not s)
total = len(results)
print(f"\n  {PASS} Passed: {passed}/{total}")
print(f"  {FAIL} Failed: {failed}/{total}")

if failed:
    print("\n  Failed:")
    for name, status, detail in results:
        if not status:
            print(f"    - {name}: {detail}")
else:
    print("\n  All LLM tests passed! Llama 3.1 70B is working.")
print()
