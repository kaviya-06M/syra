"""
SYRA End-to-End Pipeline Test
==============================
Tests the complete end-to-end flow of SYRA:
  Stage 1: Telemetry Collection (Agent Collectors)
  Stage 2: Preprocessing & Scaling
  Stage 3: ML Anomaly Detection & Failure Prediction
  Stage 4: Root Cause Reasoning Engine (Knowledge Graph + Rules)
  Stage 5: Remediation Proposal & Permission Verification
  Stage 6: LLM Explanation Generation (NVIDIA NIM Llama 3.1 70B)
  Stage 7: Response Formatting for Frontend (JSON output)
"""

import os
import sys
import json

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def log(stage, status, detail=""):
    tag = PASS if status else FAIL
    print(f"  {tag} {stage}  ->  {detail}")
    results.append((stage, status, detail))


def run_e2e_test():
    print("\n" + "=" * 75)
    print("SYRA END-TO-END PIPELINE INTEGRATION TEST")
    print("=" * 75)

    # ------------------------------------------------------------------------
    # STAGE 1: Agent Telemetry Collection
    # ------------------------------------------------------------------------
    print("\n" + "-" * 75)
    print("STAGE 1: Agent Telemetry Collection")
    print("-" * 75)

    from backend.agent.collectors.cpu_collector import CPUCollector
    from backend.agent.collectors.memory_collector import MemoryCollector
    from backend.agent.collectors.disk_collector import DiskCollector
    from backend.agent.collectors.network_collector import NetworkCollector
    from backend.agent.collectors.process_collector import ProcessCollector
    from backend.agent.collectors.windows_event_collector import WindowsEventCollector
    from backend.agent.event_generator import EventGenerator

    event_gen = EventGenerator()
    cpu_data = CPUCollector().collect()
    mem_data = MemoryCollector().collect()
    disk_data = DiskCollector().collect()
    net_data = NetworkCollector().collect()
    proc_data = ProcessCollector().collect()
    win_data = WindowsEventCollector().collect()

    live_event = event_gen.generate(cpu_data, mem_data, disk_data, net_data, proc_data, win_data)
    log("Telemetry Event Generated", "timestamp" in live_event and "cpu" in live_event,
        f"CPU={live_event['cpu']['cpu_percent']}%, RAM={live_event['memory']['memory_percent']}%")

    # ------------------------------------------------------------------------
    # STAGE 2: Preprocessing
    # ------------------------------------------------------------------------
    print("\n" + "-" * 75)
    print("STAGE 2: Preprocessing & Scaling")
    print("-" * 75)

    from backend.preprocessing.cleaner import DataCleaner
    from backend.preprocessing.feature_engineering import FeatureEngineer

    cleaner = DataCleaner()
    cleaned = cleaner.clean(live_event)
    log("Data Cleaned", isinstance(cleaned, dict), f"keys={list(cleaned.keys())}")

    engineer = FeatureEngineer()
    engineered_vector = engineer.transform(cleaned)
    log("Feature Engineering", len(engineered_vector) == 11, f"features count={len(engineered_vector)}")

    # ------------------------------------------------------------------------
    # STAGE 3: ML Inference (Anomaly Detection & Failure Prediction)
    # ------------------------------------------------------------------------
    print("\n" + "-" * 75)
    print("STAGE 3: ML Inference Engine")
    print("-" * 75)

    from backend.ml.inference.inference_engine import InferenceEngine

    ml_engine = InferenceEngine()

    # Test with an anomalous event scenario (Chrome memory spike)
    anomalous_event = {
        "timestamp": "2026-08-11T12:00:00",
        "cpu": {"cpu_percent": 92.0},
        "memory": {"memory_percent": 98.0},
        "disk": {"disk_percent": 35.0},
        "network": {"bytes_sent": 15000, "bytes_received": 45000},
        "processes": {
            "top_processes": [
                {"pid": 4092, "name": "chrome.exe", "cpu": 65.0, "memory": 78.0},
                {"pid": 1104, "name": "explorer.exe", "cpu": 2.0, "memory": 4.0},
            ]
        },
        "windows_events": [{"source": "Application", "message": "High memory pressure"}]
    }

    ml_result = ml_engine.process_snapshot(anomalous_event)
    log("ML Processing Complete", "is_anomaly" in ml_result and "risk_level" in ml_result,
        f"is_anomaly={ml_result['is_anomaly']}, failure_risk={ml_result['risk_level']}, probability={ml_result['failure_probability']}")

    # ------------------------------------------------------------------------
    # STAGE 4: Root Cause Reasoning Engine
    # ------------------------------------------------------------------------
    print("\n" + "-" * 75)
    print("STAGE 4: Root Cause Reasoning Engine (Knowledge Graph + Rules)")
    print("-" * 75)

    from backend.reasoning.root_cause_engine import RootCauseEngine

    rce = RootCauseEngine()
    diagnosis = rce.diagnose(anomalous_event, anomaly_info=ml_result)

    log("Diagnosis Complete", diagnosis["root_cause"] is not None,
        f"root_cause='{diagnosis['root_cause']}', confidence={diagnosis['confidence']}")
    log("Evidence Gathered", len(diagnosis["evidence"]) > 0,
        f"evidence={diagnosis['evidence']}")

    # ------------------------------------------------------------------------
    # STAGE 5: Remediation Executor & Permission Manager
    # ------------------------------------------------------------------------
    print("\n" + "-" * 75)
    print("STAGE 5: Remediation Engine & Verification")
    print("-" * 75)

    from backend.remediation.executor import RemediationExecutor
    from backend.remediation.verifier import RemediationVerifier

    executor = RemediationExecutor()
    proposal = executor.propose_action("action_e2e_01", root_cause=diagnosis["root_cause"], snapshot=anomalous_event)
    log("Action Proposed", "prompt" in proposal, f"prompt='{proposal['prompt'][:65]}...'")

    # User approves
    executor.permissions.respond("action_e2e_01", approved=True)
    log("User Approved Action", executor.permissions.is_approved("action_e2e_01"), "status=approved")

    # Execute action
    exec_result = executor.execute("action_e2e_01")
    log("Action Executed", exec_result.get("success", False) or "target" in exec_result or "message" in exec_result,
        f"executed action='{exec_result.get('action_id')}'")

    # Verifier check
    verifier = RemediationVerifier()
    before_snap = anomalous_event
    after_snap = {
        "cpu": {"cpu_percent": 28.0},
        "memory": {"memory_percent": 55.0},
        "disk": {"disk_percent": 35.0}
    }
    verification = verifier.verify(before_snap, after_snap, root_cause=diagnosis["root_cause"])
    log("Verification Result", verification["resolved"], f"resolved={verification['resolved']}")

    # ------------------------------------------------------------------------
    # STAGE 6: LLM Explanation Engine (NVIDIA NIM Llama 3.1 70B)
    # ------------------------------------------------------------------------
    print("\n" + "-" * 75)
    print("STAGE 6: LLM Natural Language Generation (NVIDIA NIM)")
    print("-" * 75)

    from backend.llm.explanation import ExplanationEngine
    from backend.llm.provider import LLMProvider

    try:
        provider = LLMProvider()
        explanation_engine = ExplanationEngine(provider=provider)
        print("  Calling NVIDIA NIM API (meta/llama-3.1-70b-instruct)...")

        explanation_text = explanation_engine.explain_diagnosis(diagnosis, anomaly_report=ml_result)
        log("LLM Diagnosis Explanation", len(explanation_text) > 10,
            f"length={len(explanation_text)} chars")
        print(f"\n  [LLM Output]:\n  {explanation_text}\n")

    except Exception as exc:
        log("LLM Generation", False, f"Error: {exc}")

    # ------------------------------------------------------------------------
    # STAGE 7: Response Formatter (JSON Output)
    # ------------------------------------------------------------------------
    print("\n" + "-" * 75)
    print("STAGE 7: Response Formatting (Structured JSON for Frontend)")
    print("-" * 75)

    from backend.llm.response_formatter import ResponseFormatter

    formatter = ResponseFormatter()
    formatted_output = formatter.format_diagnosis(explanation_text, diagnosis)
    json_payload = formatter.to_json(formatted_output)

    log("JSON Payload Serialized", '"type": "diagnosis"' in json_payload,
        f"payload bytes={len(json_payload)}")

    print("\n  [Final Structured JSON Payload sent to Frontend]:")
    print(json_payload)

    # ------------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------------
    print("\n" + "=" * 75)
    print("END-TO-END PIPELINE TEST SUMMARY")
    print("=" * 75)
    passed = sum(1 for _, s, _ in results if s)
    failed = sum(1 for _, s, _ in results if not s)
    total = len(results)
    print(f"\n  {PASS} Passed: {passed}/{total}")
    print(f"  {FAIL} Failed: {failed}/{total}")

    if failed == 0:
        print("\n  ALL 7 PIPELINE STAGES PASSED SUCCESSFULLY!")
    print()


if __name__ == "__main__":
    run_e2e_test()
