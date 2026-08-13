from .correlation_engine import CorrelationEngine
from .graph_traversal import GraphTraversal
from .confidence_score import ConfidenceScorer

try:
    from ml.root_cause.predictor import RootCausePredictor
except ImportError:
    RootCausePredictor = None


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
        self.ml_predictor = RootCausePredictor() if RootCausePredictor else None

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
            rule_cause, rule_confidence = None, 0.0
        else:
            rule_cause, rule_confidence = max(scores.items(), key=lambda x: x[1])

        ml_prediction = (
            self.ml_predictor.predict(event_data, anomaly_info, matched_rules)
            if self.ml_predictor else
            {"available": False, "root_cause": None, "confidence": 0.0, "probabilities": {}}
        )

        # Retain the explainable rule/graph result unless supervised ML is
        # confident and proposes a cause supported by this incident's graph.
        top_cause, top_confidence = rule_cause, rule_confidence
        ml_cause = ml_prediction.get("root_cause")
        ml_confidence = float(ml_prediction.get("confidence", 0.0))
        ml_is_compatible = (
            ml_cause in graph
            and graph.nodes[ml_cause].get("type") == "cause"
        ) if ml_cause else False
        if ml_is_compatible and ml_confidence >= 0.65 and ml_confidence > rule_confidence:
            top_cause = ml_cause
            top_confidence = round(0.60 * ml_confidence + 0.40 * rule_confidence, 3)

        evidence = self.traversal.get_upstream_symptoms(graph, top_cause) if top_cause else []
        path = self.traversal.find_path_to_cause(graph, top_cause) if top_cause else []

        # If there is no high/critical severity symptom and the ML anomaly detector
        # confirms the system is nominal (is_anomaly == False), treat system as healthy.
        has_high_severity = any(r.get("severity") in ("high", "critical") for r in matched_rules)
        is_ml_anomaly = bool(anomaly_info and anomaly_info.get("is_anomaly", False))
        if not has_high_severity and not is_ml_anomaly:
            top_cause = None
            top_confidence = 0.0
            evidence = []
            path = []

        return {
            "root_cause": top_cause,
            "confidence": top_confidence,
            "rule_root_cause": rule_cause,
            "rule_confidence": rule_confidence,
            "ml_root_cause": ml_cause,
            "ml_confidence": ml_confidence if ml_prediction.get("available") else None,
            "ml_probabilities": ml_prediction.get("probabilities", {}),
            "ml_used": top_cause == ml_cause and ml_is_compatible,
            "evidence": evidence,
            "path": path,
            "all_candidates": scores,
            "matched_rules": matched_rules,
            "graph": graph
        }
