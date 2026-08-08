from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np

try:
    from backend.ml.anomaly.anomaly_detector import AnomalyDetector
    from backend.preprocessing.feature_engineering import FeatureEngineer
except ImportError:
    from ..anomaly.anomaly_detector import AnomalyDetector
    from ...preprocessing.feature_engineering import FeatureEngineer


class FailurePredictor:
    """
    Evaluates temporal anomaly drift, resource exhaustion slopes,
    and calculates Time-To-Failure (TTF) and failure risk probability.
    """

    def __init__(
        self,
        anomaly_detector: Optional[AnomalyDetector] = None,
        history_window_size: int = 12,
        critical_error_multiplier: float = 2.5,
        memory_exhaustion_threshold: float = 95.0,
        cpu_saturation_threshold: float = 95.0,
    ):
        self.detector = anomaly_detector or AnomalyDetector()
        self.history_window_size = history_window_size
        self.critical_error_multiplier = critical_error_multiplier
        self.memory_exhaustion_threshold = memory_exhaustion_threshold
        self.cpu_saturation_threshold = cpu_saturation_threshold

        self.error_history = deque(maxlen=history_window_size)
        self.cpu_history = deque(maxlen=history_window_size)
        self.memory_history = deque(maxlen=history_window_size)
        self.disk_history = deque(maxlen=history_window_size)
        self.timestamps = deque(maxlen=history_window_size)

    def record_snapshot(self, event: Dict[str, Any]) -> None:
        """Buffers raw telemetry snapshot metrics for trend and slope regression."""
        cpu = event.get("cpu", {}).get("cpu_percent", 0.0)
        memory = event.get("memory", {}).get("memory_percent", 0.0)
        disk = event.get("disk", {}).get("disk_percent", 0.0)

        self.cpu_history.append(float(cpu or 0.0))
        self.memory_history.append(float(memory or 0.0))
        self.disk_history.append(float(disk or 0.0))
        self.timestamps.append(datetime.utcnow().timestamp())

    def predict(self, raw_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes failure risk evaluation and TTF projection from sequential events.
        """
        for ev in raw_events:
            self.record_snapshot(ev)

        # 1. Run LSTM Autoencoder anomaly detection
        anomaly_report = self.detector.detect_from_events(raw_events)
        rec_error = anomaly_report.get("reconstruction_error", 0.0)
        self.error_history.append(rec_error)

        anomaly_score = anomaly_report.get("anomaly_score", 0.0)
        is_anomaly = anomaly_report.get("is_anomaly", False)
        top_contributor = anomaly_report.get("top_contributor")

        # 2. Linear regression slope of reconstruction error and resources
        error_slope = self._calculate_slope(list(self.error_history))
        memory_slope = self._calculate_slope(list(self.memory_history))
        cpu_slope = self._calculate_slope(list(self.cpu_history))

        # 3. Calculate subsystem risk factors
        current_mem = self.memory_history[-1] if self.memory_history else 0.0
        current_cpu = self.cpu_history[-1] if self.cpu_history else 0.0
        current_disk = self.disk_history[-1] if self.disk_history else 0.0

        affected_subsystems = []
        if current_mem > 85.0 or memory_slope > 1.5 or (top_contributor and "memory" in top_contributor):
            affected_subsystems.append("Memory")
        if current_cpu > 85.0 or cpu_slope > 3.0 or (top_contributor and "cpu" in top_contributor):
            affected_subsystems.append("CPU")
        if current_disk > 90.0 or (top_contributor and "disk" in top_contributor):
            affected_subsystems.append("Disk")
        if top_contributor and "network" in top_contributor:
            affected_subsystems.append("Network")

        # 4. Estimate Time-To-Failure (TTF) in seconds
        time_to_failure_sec = None
        ttf_reasons = []

        # Check memory exhaustion trajectory
        if memory_slope > 0.1 and current_mem < self.memory_exhaustion_threshold:
            remaining_pct = self.memory_exhaustion_threshold - current_mem
            steps_to_oom = remaining_pct / memory_slope
            mem_ttf = max(10.0, steps_to_oom * 5.0)  # ~5 sec sample interval
            ttf_reasons.append(mem_ttf)

        # Check CPU persistent lockup trajectory
        if current_cpu > 92.0 and cpu_slope >= 0:
            ttf_reasons.append(45.0)

        # Critical error acceleration
        if error_slope > 0.01 and anomaly_score > 2.0:
            ttf_reasons.append(60.0)

        if ttf_reasons:
            time_to_failure_sec = round(min(ttf_reasons), 1)

        # 5. Determine overall failure probability & risk level
        probability = self._compute_failure_probability(
            anomaly_score=anomaly_score,
            error_slope=error_slope,
            memory_pct=current_mem,
            cpu_pct=current_cpu,
            memory_slope=memory_slope,
        )

        if probability >= 0.80 or (time_to_failure_sec and time_to_failure_sec <= 60):
            risk_level = "CRITICAL"
            recommended_action = "Trigger automated self-healing remediation or restart offending processes immediately."
        elif probability >= 0.55 or (time_to_failure_sec and time_to_failure_sec <= 180):
            risk_level = "HIGH"
            recommended_action = "Throttle background workloads, isolate top memory/CPU process, and alert operations."
        elif probability >= 0.30 or is_anomaly:
            risk_level = "MEDIUM"
            recommended_action = "Observe system telemetry; resource drift or mild anomaly pattern detected."
        else:
            risk_level = "LOW"
            recommended_action = "System operates within nominal parameters."

        return {
            "risk_level": risk_level,
            "failure_probability": round(probability, 3),
            "predicted_time_to_failure_seconds": time_to_failure_sec,
            "is_anomaly": is_anomaly,
            "anomaly_score": anomaly_score,
            "reconstruction_error": rec_error,
            "error_slope": round(error_slope, 5),
            "affected_subsystems": affected_subsystems if affected_subsystems else ["None"],
            "top_contributor": top_contributor,
            "recommended_action": recommended_action,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _calculate_slope(self, values: List[float]) -> float:
        """Computes ordinary least squares slope over sequential metrics."""
        if len(values) < 3:
            return 0.0
        n = len(values)
        x = np.arange(n)
        y = np.array(values, dtype=np.float32)
        slope = float(np.polyfit(x, y, 1)[0])
        return slope

    def _compute_failure_probability(
        self,
        anomaly_score: float,
        error_slope: float,
        memory_pct: float,
        cpu_pct: float,
        memory_slope: float,
    ) -> float:
        """Sigmoid-weighted probability formula fusing model error and hardware exhaustion."""
        score_component = min(1.0, anomaly_score / self.critical_error_multiplier) * 0.40
        slope_component = max(0.0, min(1.0, error_slope * 20.0)) * 0.20
        mem_component = max(0.0, (memory_pct - 60.0) / 40.0) * 0.25
        cpu_component = max(0.0, (cpu_pct - 75.0) / 25.0) * 0.15

        if memory_slope > 2.0:
            mem_component += 0.10

        prob = score_component + slope_component + mem_component + cpu_component
        return float(np.clip(prob, 0.0, 1.0))
