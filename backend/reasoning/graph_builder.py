import networkx as nx

from .knowledge_graph import KnowledgeGraph


class GraphBuilder:
    """
    Builds a live 'incident graph' for a single anomaly event by combining
    the symptoms raised by the RuleEngine with the static cause-effect
    relationships stored in the KnowledgeGraph. This is what the pipeline
    diagram calls 'Context Correlation (Rule Engine + NetworkX)'.
    """

    def __init__(self):
        self.knowledge_graph = KnowledgeGraph()

    def build(self, matched_rules, anomaly_info=None):
        """
        matched_rules: output of RuleEngine.evaluate()
        anomaly_info: optional dict from the LSTM Autoencoder,
                      e.g. {"score": 0.92, "affected_metric": "cpu"}
        """
        incident_graph = nx.DiGraph()

        incident_graph.add_node(
            "anomaly",
            type="anomaly",
            score=anomaly_info.get("score") if anomaly_info else None
        )

        kg = self.knowledge_graph.get_graph()

        for rule in matched_rules:
            symptom = rule["symptom"]

            incident_graph.add_node(
                symptom,
                type="symptom",
                severity=rule["severity"],
                weight=rule["weight"],
                rule_id=rule["rule_id"]
            )
            incident_graph.add_edge("anomaly", symptom, weight=rule["weight"])

            if symptom not in kg:
                continue

            reachable = nx.descendants(kg, symptom)
            reachable.add(symptom)
            subgraph = kg.subgraph(reachable)

            for node in subgraph.nodes:
                node_type = "symptom" if node == symptom else "cause"
                if not incident_graph.has_node(node):
                    incident_graph.add_node(node, type=node_type)

            for u, v, data in subgraph.edges(data=True):
                incident_graph.add_edge(u, v, weight=data.get("weight", 0.0))

        return incident_graph
