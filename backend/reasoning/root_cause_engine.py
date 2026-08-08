from .correlation_engine import CorrelationEngine
from .graph_traversal import GraphTraversal
from .confidence_score import ConfidenceScorer


class RootCauseEngine:
    """
    The 'Root Cause Reasoning Engine' step of the SYRA pipeline. Consumes
    a raw event snapshot + anomaly verdict, correlates it into a context
    graph, walks the graph to find candidate causes, and scores each one
    so the most likely root cause can be handed to the LLM /
    Recommendation Engine.
    """

    def __init__(self):
        self.correlation_engine = CorrelationEngine()
        self.traversal = GraphTraversal()
        self.scorer = ConfidenceScorer()

    def diagnose(self, event_data, anomaly_info=None):
        correlation = self.correlation_engine.correlate(event_data, anomaly_info)
        graph = correlation["incident_graph"]
        matched_rules = correlation["matched_rules"]

        if not matched_rules:
            return {
                "root_cause": None,
                "confidence": 0.0,
                "evidence": [],
                "matched_rules": [],
                "graph": graph
            }

        terminal_causes = self.traversal.find_terminal_causes(graph)
        reach_ranking = self.traversal.rank_causes_by_reachability(graph)

        candidates = terminal_causes or list(reach_ranking.keys())
        anomaly_score = anomaly_info.get("score") if anomaly_info else None

        scores = self.scorer.score_all(candidates, graph, reach_ranking, anomaly_score)

        if not scores:
            top_cause, top_confidence = None, 0.0
        else:
            top_cause, top_confidence = max(scores.items(), key=lambda x: x[1])

        evidence = self.traversal.get_upstream_symptoms(graph, top_cause) if top_cause else []
        path = self.traversal.find_path_to_cause(graph, top_cause) if top_cause else []

        return {
            "root_cause": top_cause,
            "confidence": top_confidence,
            "evidence": evidence,
            "path": path,
            "all_candidates": scores,
            "matched_rules": matched_rules,
            "graph": graph
        }
