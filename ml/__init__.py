"""
SYRA Machine Learning Root Package
----------------------------------
Exposes models, training, and inference pipelines.
"""

from backend.ml.models.lstm_autoencoder import LSTMAutoencoder, build_lstm_autoencoder
from backend.ml.training.dataset import TelemetryDataset, prepare_data_splits
from backend.ml.anomaly.anomaly_detector import AnomalyDetector
from backend.ml.prediction.failure_predictor import FailurePredictor

__all__ = [
    "LSTMAutoencoder",
    "build_lstm_autoencoder",
    "TelemetryDataset",
    "prepare_data_splits",
    "AnomalyDetector",
    "FailurePredictor",
]
