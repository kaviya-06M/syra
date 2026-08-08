class ConfidenceScorer:
    """
    Converts raw graph/rule signals into a single confidence score (0-1)
    for each candidate root cause, so the RootCauseEngine can decide which
    explanation to hand to the LLM / Recommendation Engine.
    """

    def __init__(self, anomaly_weight=0.4, rule_weight=0.35, reach_weight=0.25):
        self.anomaly_weight = anomaly_weight
        self.rule_weight = rule_weight
        self.reach_weight = reach_weight

    def score(self, cause, graph, reach_ranking, anomaly_score=None):
        upstream_weights = [
            graph.nodes[n].get("weight", 0.5)
            for n in graph.predecessors(cause)
            if graph.nodes[n].get("type") == "symptom"
        ]

        if not upstream_weights:
            upstream_weights = [
                graph.nodes[n].get("weight", 0.5)
                for n in graph.nodes
                if graph.nodes[n].get("type") == "symptom"
            ]

        rule_component = sum(upstream_weights) / len(upstream_weights) if upstream_weights else 0.0

        max_reach = max(reach_ranking.values()) if reach_ranking else 0
        reach_component = (reach_ranking.get(cause, 0) / max_reach) if max_reach else 0.0

        anomaly_component = anomaly_score if anomaly_score is not None else 0.5

        confidence = (
            self.anomaly_weight * anomaly_component +
            self.rule_weight * rule_component +
            self.reach_weight * reach_component
        )

        return round(min(confidence, 1.0), 3)

    def score_all(self, causes, graph, reach_ranking, anomaly_score=None):
        return {
            cause: self.score(cause, graph, reach_ranking, anomaly_score)
            for cause in causes
        }
