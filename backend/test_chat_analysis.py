import unittest

from backend.llm.explanation import ExplanationEngine


class StubProvider:
    def __init__(self):
        self.last_messages = None

    def chat(self, messages):
        self.last_messages = messages
        return "ok"


class ExplanationEngineTests(unittest.TestCase):
    def test_explain_includes_ml_analysis_payload(self):
        provider = StubProvider()
        engine = ExplanationEngine(provider=provider)
        analysis_payload = {
            "risk_level": "HIGH",
            "failure_probability": 0.82,
            "predicted_time_to_failure_seconds": 45.0,
            "is_anomaly": True,
            "anomaly_score": 3.2,
            "affected_subsystems": ["CPU", "Memory"],
            "top_contributor": "cpu",
            "recommended_action": "Throttle background workload",
        }

        engine.explain(
            user_message="Is my system healthy?",
            diagnosis={"root_cause": "CPU spike", "confidence": 0.91, "evidence": ["High CPU load"]},
            history=[],
            ml_analysis=analysis_payload,
        )

        self.assertIsNotNone(provider.last_messages)
        prompt_text = "\n".join(message["content"] for message in provider.last_messages if message["role"] == "user")
        self.assertIn("risk_level", prompt_text)
        self.assertIn("HIGH", prompt_text)
        self.assertIn("0.82", prompt_text)


if __name__ == "__main__":
    unittest.main()
