import json
import os
from typing import Any, Dict, List, Optional
import numpy as np


def compute_threshold_stats(
    reconstruction_errors: List[float],
    percentile: float = 99.0,
    std_multiplier: float = 3.0,
) -> Dict[str, float]:
    """
    Computes statistical anomaly threshold metrics from validation errors.
    """
    if not reconstruction_errors:
        return {
            "threshold": 0.05,
            "mean_error": 0.01,
            "std_error": 0.01,
            "max_error": 0.05,
            "percentile": 0.05,
        }

    errors = np.asarray(reconstruction_errors, dtype=np.float32)
    mean_err = float(np.mean(errors))
    std_err = float(np.std(errors))
    pct_err = float(np.percentile(errors, percentile))
    max_err = float(np.max(errors))

    # Dynamic threshold based on the LSTM reconstruction-error distribution
    # rather than a manually fixed value. This is derived from validation data.
    threshold = float(max(pct_err, mean_err + (std_multiplier * std_err)))

    return {
        "threshold": round(threshold, 6),
        "mean_error": round(mean_err, 6),
        "std_error": round(std_err, 6),
        "max_error": round(max_err, 6),
        "percentile": round(pct_err, 6),
    }


class AnomalyThreshold:
    """
    Manages loading, saving, and evaluating anomaly thresholds.
    """

    def __init__(
        self,
        filepath: str = "backend/ml/saved_models/threshold.json",
        default_threshold: float = 0.05,
    ):
        self.filepath = filepath
        self.default_threshold = default_threshold
        self.threshold = default_threshold
        self.stats: Dict[str, Any] = {}
        self.load()

    def is_anomaly(self, reconstruction_error: float) -> bool:
        """Returns True if the reconstruction error exceeds the dynamically derived threshold."""
        return float(reconstruction_error) > self.threshold

    def save(self, stats: Optional[Dict[str, float]] = None) -> None:
        """Saves threshold statistics to disk."""
        if stats is not None:
            self.stats = stats
            self.threshold = float(stats.get("threshold", self.default_threshold))

        os.makedirs(os.path.dirname(os.path.abspath(self.filepath)), exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump({
                "threshold": self.threshold,
                **self.stats,
            }, f, indent=2)

    def load(self) -> None:
        """Loads threshold configuration from disk."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    data = json.load(f)
                    self.stats = data
                    self.threshold = float(data.get("threshold", self.default_threshold))
            except Exception as e:
                print(f"[AnomalyThreshold] Warning: Could not load threshold from {self.filepath}: {e}")
                self.threshold = self.default_threshold
        else:
            self.threshold = self.default_threshold
