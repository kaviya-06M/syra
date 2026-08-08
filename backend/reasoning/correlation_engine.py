from .rule_engine import RuleEngine
from .graph_builder import GraphBuilder


class CorrelationEngine:
    """
    Implements the 'Context Correlation (Rule Engine + NetworkX)' step of
    the SYRA pipeline. Takes the raw event snapshot produced by the
    Background Agent plus the anomaly verdict from the LSTM Autoencoder,
    and returns a correlated incident graph ready for root cause analysis.
    """

    def __init__(self):
        self.rule_engine = RuleEngine()
        self.graph_builder = GraphBuilder()

    def correlate(self, event_data, anomaly_info=None):
        matched_rules = self.rule_engine.evaluate(event_data)

        incident_graph = self.graph_builder.build(
            matched_rules=matched_rules,
            anomaly_info=anomaly_info
        )

        return {
            "matched_rules": matched_rules,
            "incident_graph": incident_graph
        }
