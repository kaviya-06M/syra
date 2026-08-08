"""
SYRA Reasoning Layer Test
=========================
Tests the full reasoning pipeline:
  RuleEngine -> GraphBuilder -> GraphTraversal -> ConfidenceScorer -> RootCauseEngine

Scenario 1: Normal system (nothing fires)
Scenario 2: High memory + runaway process (your chrome.exe example)
Scenario 3: Live data from your machine
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []

def log(stage, status, detail=""):
    tag = PASS if status else FAIL
    msg = f"  {tag} {stage}"
    if detail:
        msg += f"  ->  {detail}"
    print(msg)
    results.append((stage, status, detail))


# ============================================================================
# TEST 1: RuleEngine with normal data (nothing should fire)
# ============================================================================
print("\n" + "=" * 70)
print("TEST 1: RuleEngine - Normal system (no rules should fire)")
print("=" * 70)

from backend.reasoning.rule_engine import RuleEngine

engine = RuleEngine()
normal_event = {
    "cpu": {"cpu_percent": 25},
    "memory": {"memory_percent": 45},
    "disk": {"disk_percent": 30},
    "network": {"bytes_sent": 1000, "bytes_received": 5000},
    "processes": {"top_processes": [{"name": "explorer.exe", "cpu": 2, "memory": 5}]},
    "windows_events": []
}

matched = engine.evaluate(normal_event)
log("Normal event", len(matched) == 0, f"rules fired={len(matched)} (expected 0)")


# ============================================================================
# TEST 2: RuleEngine with anomalous data (your chrome example)
# ============================================================================
print("\n" + "=" * 70)
print("TEST 2: RuleEngine - Chrome eating memory (multiple rules fire)")
print("=" * 70)

anomalous_event = {
    "cpu": {"cpu_percent": 92},
    "memory": {"memory_percent": 98},
    "disk": {"disk_percent": 30},
    "network": {"bytes_sent": 1000, "bytes_received": 5000},
    "processes": {"top_processes": [
        {"name": "chrome.exe", "cpu": 55, "memory": 72},
        {"name": "explorer.exe", "cpu": 1, "memory": 3}
    ]},
    "windows_events": [{"source": "Application", "message": "memory pressure"}]
}

matched = engine.evaluate(anomalous_event)
fired_ids = [r["rule_id"] for r in matched]
log("HIGH_CPU fires", "HIGH_CPU" in fired_ids, f"cpu=92%")
log("HIGH_MEMORY fires", "HIGH_MEMORY" in fired_ids, f"memory=98%")
log("RUNAWAY_PROCESS fires", "RUNAWAY_PROCESS" in fired_ids, f"chrome cpu=55, mem=72")
log("WINDOWS_ERROR fires", "WINDOWS_ERROR_EVENTS" in fired_ids, f"1 event")
log("LOW_DISK does NOT fire", "LOW_DISK_SPACE" not in fired_ids, f"disk=30% (below 90)")
log("Total rules", len(matched) == 4, f"fired={len(matched)}, IDs={fired_ids}")

for r in matched:
    print(f"    {r['rule_id']:25s} symptom={r['symptom']:25s} severity={r['severity']} weight={r['weight']}")


# ============================================================================
# TEST 3: KnowledgeGraph (static domain knowledge)
# ============================================================================
print("\n" + "=" * 70)
print("TEST 3: KnowledgeGraph - Static cause-effect relationships")
print("=" * 70)

from backend.reasoning.knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()
graph = kg.get_graph()

log("Graph loaded", graph.number_of_nodes() > 0, f"nodes={graph.number_of_nodes()}, edges={graph.number_of_edges()}")

# Trace: high_memory_usage -> memory_leak -> system_slowdown
mem_causes = kg.get_related_causes("high_memory_usage")
log("Memory cause chain", "memory_leak" in mem_causes and "system_slowdown" in mem_causes,
    f"high_memory_usage -> {mem_causes}")

# Trace: high_cpu_usage -> runaway_process -> cpu_bottleneck -> system_slowdown
cpu_causes = kg.get_related_causes("high_cpu_usage")
log("CPU cause chain", "cpu_bottleneck" in cpu_causes and "system_slowdown" in cpu_causes,
    f"high_cpu_usage -> {cpu_causes}")

w = kg.get_edge_weight("high_memory_usage", "memory_leak")
log("Edge weight", w == 0.6, f"high_memory_usage->memory_leak = {w}")


# ============================================================================
# TEST 4: GraphBuilder (incident graph from matched rules)
# ============================================================================
print("\n" + "=" * 70)
print("TEST 4: GraphBuilder - Build incident graph from anomaly")
print("=" * 70)

from backend.reasoning.graph_builder import GraphBuilder

builder = GraphBuilder()
anomaly_info = {"score": 0.87}
incident_graph = builder.build(matched_rules=matched, anomaly_info=anomaly_info)

log("Incident graph", incident_graph.number_of_nodes() > 0,
    f"nodes={incident_graph.number_of_nodes()}, edges={incident_graph.number_of_edges()}")

# Check node types
anomaly_nodes = [n for n, d in incident_graph.nodes(data=True) if d.get("type") == "anomaly"]
symptom_nodes = [n for n, d in incident_graph.nodes(data=True) if d.get("type") == "symptom"]
cause_nodes = [n for n, d in incident_graph.nodes(data=True) if d.get("type") == "cause"]

log("Anomaly node exists", len(anomaly_nodes) == 1, f"anomaly nodes={anomaly_nodes}")
log("Symptom nodes", len(symptom_nodes) >= 3, f"symptoms={symptom_nodes}")
log("Cause nodes", len(cause_nodes) >= 1, f"causes={cause_nodes}")

print(f"\n  Incident graph structure:")
for u, v, d in incident_graph.edges(data=True):
    print(f"    {u:30s} -> {v:30s} (weight={d.get('weight', 0)})")


# ============================================================================
# TEST 5: GraphTraversal
# ============================================================================
print("\n" + "=" * 70)
print("TEST 5: GraphTraversal - Find terminal causes and paths")
print("=" * 70)

from backend.reasoning.graph_traversal import GraphTraversal

traversal = GraphTraversal()

terminals = traversal.find_terminal_causes(incident_graph)
log("Terminal causes found", len(terminals) >= 1, f"terminals={terminals}")

ranking = traversal.rank_causes_by_reachability(incident_graph)
log("Reachability ranking", len(ranking) >= 1, f"ranking={ranking}")

if terminals:
    path = traversal.find_path_to_cause(incident_graph, terminals[0])
    log("Path to top cause", len(path) >= 2, f"path={path}")

    upstream = traversal.get_upstream_symptoms(incident_graph, terminals[0])
    log("Upstream symptoms", len(upstream) >= 1, f"symptoms={upstream}")


# ============================================================================
# TEST 6: ConfidenceScorer
# ============================================================================
print("\n" + "=" * 70)
print("TEST 6: ConfidenceScorer - Score candidate causes")
print("=" * 70)

from backend.reasoning.confidence_score import ConfidenceScorer

scorer = ConfidenceScorer()
scores = scorer.score_all(terminals, incident_graph, ranking, anomaly_score=0.87)
log("Scores computed", len(scores) >= 1, f"scores={scores}")

for cause, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
    print(f"    {cause:30s} confidence={score}")


# ============================================================================
# TEST 7: RootCauseEngine (full pipeline)
# ============================================================================
print("\n" + "=" * 70)
print("TEST 7: RootCauseEngine - Full diagnosis (your chrome example)")
print("=" * 70)

from backend.reasoning.root_cause_engine import RootCauseEngine

rce = RootCauseEngine()
diagnosis = rce.diagnose(anomalous_event, anomaly_info={"score": 0.87})

log("Root cause found", diagnosis["root_cause"] is not None,
    f"root_cause={diagnosis['root_cause']}")
log("Confidence > 0", diagnosis["confidence"] > 0,
    f"confidence={diagnosis['confidence']}")
log("Evidence present", len(diagnosis["evidence"]) >= 1,
    f"evidence={diagnosis['evidence']}")
log("Path traced", len(diagnosis["path"]) >= 2,
    f"path={diagnosis['path']}")

print(f"\n  DIAGNOSIS RESULT:")
print(f"    Root cause:  {diagnosis['root_cause']}")
print(f"    Confidence:  {diagnosis['confidence']}")
print(f"    Evidence:    {diagnosis['evidence']}")
print(f"    Path:        {diagnosis['path']}")
print(f"    Candidates:  {diagnosis['all_candidates']}")
print(f"    Rules fired: {[r['rule_id'] for r in diagnosis['matched_rules']]}")


# ============================================================================
# TEST 8: Normal data -> no root cause
# ============================================================================
print("\n" + "=" * 70)
print("TEST 8: RootCauseEngine - Normal system (no diagnosis)")
print("=" * 70)

normal_diag = rce.diagnose(normal_event, anomaly_info={"score": 0.05})
log("No root cause", normal_diag["root_cause"] is None, f"root_cause={normal_diag['root_cause']}")
log("Zero confidence", normal_diag["confidence"] == 0.0, f"confidence={normal_diag['confidence']}")


# ============================================================================
# TEST 9: Live data from your machine
# ============================================================================
print("\n" + "=" * 70)
print("TEST 9: RootCauseEngine - Live system data")
print("=" * 70)

from backend.agent.event_generator import EventGenerator
from backend.agent.collectors.cpu_collector import CPUCollector
from backend.agent.collectors.memory_collector import MemoryCollector
from backend.agent.collectors.disk_collector import DiskCollector
from backend.agent.collectors.network_collector import NetworkCollector
from backend.agent.collectors.process_collector import ProcessCollector
from backend.agent.collectors.windows_event_collector import WindowsEventCollector

gen = EventGenerator()
live_event = gen.generate(
    CPUCollector().collect(),
    MemoryCollector().collect(),
    DiskCollector().collect(),
    NetworkCollector().collect(),
    ProcessCollector().collect(),
    WindowsEventCollector().collect(),
)

live_diag = rce.diagnose(live_event, anomaly_info={"score": 0.5})
log("Live diagnosis runs", isinstance(live_diag, dict), f"root_cause={live_diag['root_cause']}")

rules_fired = [r["rule_id"] for r in live_diag["matched_rules"]]
print(f"  Live rules fired: {rules_fired}")
print(f"  Live root cause:  {live_diag['root_cause']}")
print(f"  Live confidence:  {live_diag['confidence']}")
if live_diag["evidence"]:
    print(f"  Live evidence:    {live_diag['evidence']}")


# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("REASONING LAYER TEST SUMMARY")
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
    print("\n  All reasoning tests passed!")
print()
