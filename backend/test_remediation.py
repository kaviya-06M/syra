"""
SYRA Remediation Layer Test
============================
Tests the full remediation pipeline:
  PermissionManager -> RemediationActions -> RemediationExecutor
  -> RemediationVerifier -> RollbackManager

Does NOT actually kill processes or delete files - tests logic flow only.
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
# TEST 1: PermissionManager
# ============================================================================
print("\n" + "=" * 70)
print("TEST 1: PermissionManager - request / approve / deny flow")
print("=" * 70)

from backend.remediation.permissions import PermissionManager

pm = PermissionManager()

# Request permission
req = pm.request_permission(
    action_id="action_001",
    action_name="kill_top_process",
    root_cause="cpu_bottleneck",
    description="This will close the process using the most resources."
)
log("Request permission", "prompt" in req and "action_001" in req["action_id"],
    f"prompt='{req['prompt'][:60]}...'")

# Not yet approved
log("Pending (not approved)", not pm.is_approved("action_001"), "status=pending")

# User says Yes
resp = pm.respond("action_001", approved=True)
log("User approves", pm.is_approved("action_001"), f"status={resp['status']}")

# Request another, user says No
pm.request_permission("action_002", "clear_temp_files", "disk_io_bottleneck", "Delete temp files.")
pm.respond("action_002", approved=False)
log("User denies", pm.is_denied("action_002"), "status=denied")

# Clear
pm.clear("action_001")
log("Clear after execute", not pm.is_approved("action_001"), "cleared from pending")

# Unknown action_id
resp = pm.respond("nonexistent", approved=True)
log("Unknown action_id", not resp["success"], f"message={resp['message']}")


# ============================================================================
# TEST 2: RemediationActions (safe tests only)
# ============================================================================
print("\n" + "=" * 70)
print("TEST 2: RemediationActions - verify method signatures")
print("=" * 70)

from backend.remediation.actions import RemediationActions

actions = RemediationActions()

# kill_top_process with invalid PID (should fail gracefully)
result = actions.kill_top_process(pid=999999999)
log("kill_top_process (bad pid)", not result["success"], f"message={result['message']}")

# flush_dns - just check it returns a result dict
result = actions.flush_dns()
log("flush_dns returns dict", "action" in result and result["action"] == "flush_dns",
    f"success={result['success']}, message={result['message']}")

# free_memory - runs EmptyWorkingSet on background procs
result = actions.free_memory()
log("free_memory runs", result["success"], f"message={result['message']}")


# ============================================================================
# TEST 3: RemediationExecutor - propose and execute flow
# ============================================================================
print("\n" + "=" * 70)
print("TEST 3: RemediationExecutor - propose / approve / execute")
print("=" * 70)

from backend.remediation.executor import RemediationExecutor, ACTION_MAP

executor = RemediationExecutor()

# Check ACTION_MAP covers key root causes
expected_causes = ["cpu_bottleneck", "memory_leak", "excessive_swapping",
                   "disk_io_bottleneck", "network_congestion", "system_slowdown"]
for cause in expected_causes:
    log(f"ACTION_MAP has '{cause}'", cause in ACTION_MAP, f"action={ACTION_MAP.get(cause)}")

# Propose action for a root cause
proposal = executor.propose_action("fix_001", root_cause="cpu_bottleneck")
log("Propose action", "prompt" in proposal, f"prompt='{proposal['prompt'][:60]}...'")

# Try to execute WITHOUT approval -> should fail
result = executor.execute("fix_001", root_cause="cpu_bottleneck", pid=999999999)
log("Execute without approval", not result["success"], f"message={result['message']}")

# Approve then execute (with bad PID so it fails safely)
executor.permissions.respond("fix_001", approved=True)
result = executor.execute("fix_001", root_cause="cpu_bottleneck", pid=999999999)
log("Execute after approval", not result["success"],
    f"Correctly tried and failed: {result['message']}")

# Unknown root cause
proposal2 = executor.propose_action("fix_002", root_cause="alien_invasion")
log("Unknown root cause", not proposal2["success"], f"message={proposal2['message']}")

# History tracking
last = executor.get_last_action()
log("History tracked", last is not None, f"last action={last['action'] if last else None}")


# ============================================================================
# TEST 4: RemediationVerifier
# ============================================================================
print("\n" + "=" * 70)
print("TEST 4: RemediationVerifier - before/after comparison")
print("=" * 70)

from backend.remediation.verifier import RemediationVerifier

verifier = RemediationVerifier()

# Scenario: Memory dropped from 98% to 61% (your chrome example)
before = {"cpu": {"cpu_percent": 92}, "memory": {"memory_percent": 98}, "disk": {"disk_percent": 30}}
after = {"cpu": {"cpu_percent": 35}, "memory": {"memory_percent": 61}, "disk": {"disk_percent": 30}}

v = verifier.verify(before, after, root_cause="memory_leak")
log("Memory fix verified", v["resolved"], f"resolved={v['resolved']}, checks={v['checks']}")
log("Not still critical", not v["still_critical"], f"still_critical={v['still_critical']}")

# Scenario: Nothing improved
after_same = {"cpu": {"cpu_percent": 91}, "memory": {"memory_percent": 97}, "disk": {"disk_percent": 30}}
v2 = verifier.verify(before, after_same, root_cause="memory_leak")
log("No improvement", not v2["resolved"], f"resolved={v2['resolved']}, still_critical={v2['still_critical']}")

# Scenario: Improved but still critical (dropped 98 -> 88, still above 85)
after_partial = {"cpu": {"cpu_percent": 40}, "memory": {"memory_percent": 88}, "disk": {"disk_percent": 30}}
v3 = verifier.verify(before, after_partial, root_cause="memory_leak")
log("Partial fix (still critical)", not v3["resolved"],
    f"improved but still_critical={v3['still_critical']}")


# ============================================================================
# TEST 5: RollbackManager
# ============================================================================
print("\n" + "=" * 70)
print("TEST 5: RollbackManager - rollback actions")
print("=" * 70)

from backend.remediation.rollback import RollbackManager

rollback = RollbackManager()

# kill_top_process -> cannot be rolled back
r1 = rollback.rollback({"action": "kill_top_process", "target": {"pid": 123, "name": "test.exe"}})
log("Kill process rollback", not r1["success"], f"message={r1['message'][:50]}...")

# clear_temp_files -> noop
r2 = rollback.rollback({"action": "clear_temp_files"})
log("Clear temp rollback", r2["success"], f"message={r2['message']}")

# flush_dns -> noop
r3 = rollback.rollback({"action": "flush_dns"})
log("DNS flush rollback", r3["success"], f"message={r3['message']}")

# free_memory -> noop
r4 = rollback.rollback({"action": "free_memory"})
log("Free memory rollback", r4["success"], f"message={r4['message']}")

# Unknown action -> noop fallback
r5 = rollback.rollback({"action": "unknown_action"})
log("Unknown action rollback", r5["success"], f"message={r5['message']}")


# ============================================================================
# TEST 6: Full end-to-end flow (simulated)
# ============================================================================
print("\n" + "=" * 70)
print("TEST 6: Full remediation flow (simulated chrome scenario)")
print("=" * 70)

print("""
  Simulating your architecture flow:
    RootCauseEngine says: root_cause='system_slowdown', confidence=0.826
    -> Executor proposes: kill_top_process
    -> User approves
    -> Execute (simulated)
    -> Verifier checks before/after
    -> RESOLVED
""")

# Step 1: Propose
exec2 = RemediationExecutor()
proposal = exec2.propose_action("chrome_fix", root_cause="system_slowdown")
log("Step 1: Propose", "prompt" in proposal, f"action=kill_top_process")
print(f"    SYRA says: \"{proposal['prompt']}\"")

# Step 2: User approves
exec2.permissions.respond("chrome_fix", approved=True)
log("Step 2: User approves", exec2.permissions.is_approved("chrome_fix"), "approved=True")

# Step 3: Verify before/after
before = {"cpu": {"cpu_percent": 92}, "memory": {"memory_percent": 98}, "disk": {"disk_percent": 30}}
after = {"cpu": {"cpu_percent": 35}, "memory": {"memory_percent": 61}, "disk": {"disk_percent": 30}}
v = verifier.verify(before, after, root_cause="system_slowdown")
log("Step 3: Verify", v["resolved"], f"98% -> 61% = RESOLVED")

print(f"\n    SYRA says: \"The system has returned to a healthier state.\"")
print(f"    SYRA says: \"Memory usage dropped from 98% to 61%.\"")


# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("REMEDIATION LAYER TEST SUMMARY")
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
    print("\n  All remediation tests passed!")
print()
