"""
SYRA Machine Learning Root Package
----------------------------------
Exposes models, training, and inference pipelines.
"""

from backend.ml.models.lstm_autoencoder import LSTMAutoencoder, Encoder, Decoder
from backend.ml.training.dataset import SystemMetricsDataset, create_dataloaders
from backend.ml.training.train import train_model, ModelTrainer
from backend.ml.inference.anomaly_detector import AnomalyDetector
from backend.ml.inference.failure_predictor import FailurePredictor

__all__ = [
    "LSTMAutoencoder",
    "Encoder",
    "Decoder",
    "SystemMetricsDataset",
    "create_dataloaders",
    "train_model",
    "ModelTrainer",
    "AnomalyDetector",
    "FailurePredictor",
]
