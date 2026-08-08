"""
SYRA Machine Learning Subsystem
-------------------------------
Provides multivariate time-series anomaly detection, LSTM Autoencoder architectures,
proactive failure prediction, and statistical thresholding.
"""

from .models.lstm_autoencoder import LSTMAutoencoder, build_lstm_autoencoder
from .anomaly.anomaly_detector import AnomalyDetector
from .prediction.failure_predictor import FailurePredictor
from .inference.inference_engine import InferenceEngine
from .training.dataset import TelemetryDataset, prepare_data_splits
from .training.train import train_lstm_autoencoder
from .utils.metrics import compute_reconstruction_metrics, compute_feature_contributions
from .utils.threshold import AnomalyThreshold, compute_threshold_stats

__all__ = [
    "LSTMAutoencoder",
    "build_lstm_autoencoder",
    "AnomalyDetector",
    "FailurePredictor",
    "InferenceEngine",
    "TelemetryDataset",
    "prepare_data_splits",
    "train_lstm_autoencoder",
    "compute_reconstruction_metrics",
    "compute_feature_contributions",
    "AnomalyThreshold",
    "compute_threshold_stats",
]
