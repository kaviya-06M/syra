"""
SYRA Frontend <-> Backend API Communication Test
=================================================
Verifies that all API routes expected by the frontend respond correctly:
  - GET  /api/health
  - GET  /api/metrics/current
  - POST /api/diagnosis/analyze
  - GET  /api/diagnosis/latest
  - POST /api/remediation/propose
  - POST /api/remediation/approve
  - POST /api/remediation/execute
  - POST /api/chat/message
  - GET  /api/history/stats
  - GET  /api/history/incidents
"""

import os
import sys
import unittest.mock as mock

# Ensure backend directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def log(endpoint, status, detail=""):
    tag = PASS if status else FAIL
    print(f"  {tag} {endpoint:35s} -> {detail}")
    results.append((endpoint, status, detail))


def test_api_communication():
    print("\n" + "=" * 75)
    print("SYRA FRONTEND <-> BACKEND COMMUNICATION API TEST")
    print("=" * 75)

    client = TestClient(app)

    # 1. GET /api/health
    r = client.get("/api/health")
    log("GET /api/health", r.status_code == 200 and r.json().get("status") == "ok",
        f"status={r.status_code}, response={r.json()}")

    # 2. GET /api/metrics/current
    r = client.get("/api/metrics/current")
    log("GET /api/metrics/current", r.status_code == 200,
        f"status={r.status_code}, keys={list(r.json().keys()) if isinstance(r.json(), dict) else 'msg'}")

    # 3. POST /api/diagnosis/analyze with sample event data
    sample_event = {
        "timestamp": "2026-08-11T12:00:00",
        "cpu": {"cpu_percent": 90.0},
        "memory": {"memory_percent": 95.0},
        "disk": {"disk_percent": 30.0},
        "network": {"bytes_sent": 1000, "bytes_received": 2000},
        "processes": {
            "top_processes": [
                {"pid": 1234, "name": "chrome.exe", "cpu": 55.0, "memory": 70.0}
            ]
        },
        "windows_events": []
    }
    r = client.post("/api/diagnosis/analyze", json={"event_data": sample_event})
    log("POST /api/diagnosis/analyze", r.status_code == 200 and "root_cause" in r.json(),
        f"root_cause='{r.json().get('root_cause')}', confidence={r.json().get('confidence')}")

    # 4. GET /api/diagnosis/latest
    r = client.get("/api/diagnosis/latest")
    log("GET /api/diagnosis/latest", r.status_code == 200 and r.json().get("root_cause") is not None,
        f"latest root_cause='{r.json().get('root_cause')}'")

    # Populate metrics history for remediation target selection
    from api.routes.metrics import record_snapshot
    record_snapshot(sample_event)

    # 5. POST /api/remediation/propose
    r = client.post("/api/remediation/propose", json={"root_cause": "system_slowdown"})
    res_data = r.json()
    action_id = res_data.get("action_id") if isinstance(res_data, dict) else None
    log("POST /api/remediation/propose", r.status_code == 200 and action_id is not None,
        f"action_id='{action_id}', action='{res_data.get('action')}'")

    # 6. POST /api/remediation/approve
    r = client.post("/api/remediation/approve", json={"action_id": action_id, "approved": True})
    log("POST /api/remediation/approve", r.status_code == 200 and r.json().get("status") == "approved",
        f"status={r.json().get('status')}")

    # 7. POST /api/remediation/execute
    r = client.post("/api/remediation/execute", json={"action_id": action_id})
    log("POST /api/remediation/execute", r.status_code == 200,
        f"action_id='{r.json().get('action_id')}', message='{r.json().get('message')}'")

    # 8. POST /api/chat/message (with mocked LLM for instant response)
    with mock.patch("llm.explanation.ExplanationEngine.explain", return_value="Root cause: system_slowdown. High memory usage detected."):
        r = client.post("/api/chat/message", json={"message": "What is wrong with my PC?"})
        log("POST /api/chat/message", r.status_code == 200 and "reply" in r.json(),
            f"reply='{r.json().get('reply')[:60]}...'")

    # 9. GET /api/history/stats
    r = client.get("/api/history/stats")
    log("GET /api/history/stats", r.status_code == 200 and "total_incidents" in r.json(),
        f"stats={r.json()}")

    # 10. GET /api/history/incidents
    r = client.get("/api/history/incidents")
    log("GET /api/history/incidents", r.status_code == 200 and isinstance(r.json(), list),
        f"incidents count={len(r.json())}")

    # SUMMARY
    print("\n" + "=" * 75)
    print("API COMMUNICATION TEST SUMMARY")
    print("=" * 75)
    passed = sum(1 for _, s, _ in results if s)
    failed = sum(1 for _, s, _ in results if not s)
    total = len(results)
    print(f"\n  {PASS} Passed: {passed}/{total}")
    print(f"  {FAIL} Failed: {failed}/{total}")

    if failed == 0:
        print("\n  ALL API COMMUNICATION ENDPOINTS PASSED SUCCESSFULLY!")
    print()


if __name__ == "__main__":
    test_api_communication()
