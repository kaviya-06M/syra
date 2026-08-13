import os
from collections import deque
from typing import Any, Dict, List, Optional
import numpy as np

try:
    from backend.ml.models.lstm_autoencoder import LSTMAutoencoder
    from backend.ml.utils.metrics import compute_feature_contributions, compute_anomaly_score
    from backend.ml.utils.threshold import AnomalyThreshold, compute_threshold_stats
    from backend.preprocessing.cleaner import DataCleaner
    from backend.preprocessing.feature_engineering import FeatureEngineer
    from backend.preprocessing.scaler import FeatureScaler
    from backend.preprocessing.sequence_builder import SequenceBuilder
except ImportError:
    from ..models.lstm_autoencoder import LSTMAutoencoder
    from ..utils.metrics import compute_feature_contributions, compute_anomaly_score
    from ..utils.threshold import AnomalyThreshold, compute_threshold_stats
    from ...preprocessing.cleaner import DataCleaner
    from ...preprocessing.feature_engineering import FeatureEngineer
    from ...preprocessing.scaler import FeatureScaler
    from ...preprocessing.sequence_builder import SequenceBuilder


class AnomalyDetector:
    """
    Evaluates telemetry sequences using the trained LSTM Autoencoder.
    Measures reconstruction error against the anomaly threshold and
    pinpoints the specific subsystem responsible for the anomalous pattern.
    """

    def __init__(
        self,
        model_path: str = "backend/ml/saved_models/lstm_autoencoder.keras",
        scaler_path: str = "backend/ml/saved_models/feature_scaler.pkl",
        threshold_path: str = "backend/ml/saved_models/threshold.json",
        default_threshold: float = 0.05,
        sequence_length: int = 10,
    ):
        self.sequence_length = sequence_length
        self.cleaner = DataCleaner()
        self.engineer = FeatureEngineer()
        self.scaler = FeatureScaler(model_path=scaler_path)
        self.threshold_mgr = AnomalyThreshold(
            filepath=threshold_path,
            default_threshold=default_threshold,
        )
        self.reconstruction_error_history: deque[float] = deque(maxlen=50)
        self.autoencoder = LSTMAutoencoder(
            timesteps=sequence_length,
            n_features=self.engineer.feature_count(),
            model_path=model_path,
        )

        # Attempt to load scaler if present
        if os.path.exists(scaler_path):
            try:
                self.scaler.load()
            except Exception as e:
                print(f"[AnomalyDetector] Note on scaler load: {e}")

    @property
    def threshold(self) -> float:
        return self.threshold_mgr.threshold

    def detect_from_events(self, raw_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes anomaly detection on a rolling window of raw event snapshots.
        """
        if len(raw_events) < self.sequence_length:
            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "reconstruction_error": 0.0,
                "threshold": self.threshold,
                "confidence": 0.0,
                "message": f"Buffering telemetry: {len(raw_events)}/{self.sequence_length} collected",
                "contributing_features": [],
            }

        # Clean and engineer features
        recent_events = raw_events[-self.sequence_length:]
        cleaned = [self.cleaner.clean(e) for e in recent_events]
        features = [self.engineer.transform(e) for e in cleaned]
        feature_array = np.asarray(features, dtype=np.float32)

        # Scale features
        try:
            scaled = self.scaler.transform(feature_array)
        except Exception:
            min_val = np.min(feature_array, axis=0, keepdims=True)
            max_val = np.max(feature_array, axis=0, keepdims=True)
            denom = np.where((max_val - min_val) == 0, 1.0, (max_val - min_val))
            scaled = (feature_array - min_val) / denom

        # Shape: (1, sequence_length, n_features)
        seq_window = np.expand_dims(scaled, axis=0)
        return self.detect(seq_window)

    def detect(self, sequence_window: np.ndarray) -> Dict[str, Any]:
        """
        Runs reconstruction inference on a window of scaled features.
        """
        seq = np.asarray(sequence_window, dtype=np.float32)
        if seq.ndim == 2:
            seq = np.expand_dims(seq, axis=0)

        reconstructed = self.autoencoder.reconstruct(seq)
        rec_error = float(np.mean((seq - reconstructed) ** 2))
        self.reconstruction_error_history.append(rec_error)

        # Derive the anomaly threshold from the LSTM reconstruction-error history
        # at runtime instead of relying on a manually fixed constant.
        stats = compute_threshold_stats(list(self.reconstruction_error_history))
        derived_threshold = max(self.threshold, stats["threshold"])
        if len(self.reconstruction_error_history) < 3:
            derived_threshold = max(self.threshold, rec_error * 1.5 + 1e-6)

        is_anomaly = rec_error > derived_threshold
        anomaly_score = compute_anomaly_score(rec_error, derived_threshold)

        # Feature contribution breakdown
        feature_names = self.engineer.feature_names()
        contributions = compute_feature_contributions(seq, reconstructed, feature_names)
        top_feature = contributions[0]["feature"] if contributions else None

        confidence = round(min(1.0, max(0.0, (anomaly_score - 0.5) / 1.5)), 2) if is_anomaly else 0.95

        return {
            "is_anomaly": bool(is_anomaly),
            "anomaly_score": anomaly_score,
            "reconstruction_error": round(rec_error, 6),
            "threshold": round(derived_threshold, 6),
            "confidence": confidence,
            "top_contributor": top_feature,
            "contributing_features": contributions,
        }
