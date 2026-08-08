from typing import Any, Dict, List, Optional

try:
    from backend.ml.anomaly.anomaly_detector import AnomalyDetector
    from backend.ml.prediction.failure_predictor import FailurePredictor
except ImportError:
    from ..anomaly.anomaly_detector import AnomalyDetector
    from ..prediction.failure_predictor import FailurePredictor


class InferenceEngine:
    """
    Central inference engine orchestrating multivariate anomaly detection
    and proactive failure prediction on live telemetry snapshots.
    """

    def __init__(
        self,
        anomaly_detector: Optional[AnomalyDetector] = None,
        failure_predictor: Optional[FailurePredictor] = None,
    ):
        self.anomaly_detector = anomaly_detector or AnomalyDetector()
        self.failure_predictor = failure_predictor or FailurePredictor(
            anomaly_detector=self.anomaly_detector
        )
        self.event_buffer: List[Dict[str, Any]] = []
        self.buffer_size: int = 20

    def process_snapshot(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Receives a single live event snapshot from the agent scheduler,
        updates internal history buffer, and runs real-time inference.
        """
        self.event_buffer.append(event)
        if len(self.event_buffer) > self.buffer_size:
            self.event_buffer.pop(0)

        return self.process_telemetry(self.event_buffer)

    def process_telemetry(self, raw_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Runs unified anomaly detection and failure forecasting across telemetry events.
        """
        prediction_report = self.failure_predictor.predict(raw_events)
        return prediction_report
