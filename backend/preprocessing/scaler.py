import os
import joblib
import numpy as np
from sklearn.preprocessing import MinMaxScaler


class FeatureScaler:
    """
    Wraps a sklearn MinMaxScaler so feature vectors are scaled to [0, 1]
    before being fed into the LSTM Autoencoder. The fitted scaler is
    persisted to disk so training-time scaling and inference-time
    scaling always stay in sync.
    """

    def __init__(self, model_path="backend/ml/saved_models/feature_scaler.pkl"):
        self.model_path = model_path
        self.scaler = None

    def fit(self, feature_matrix):
        """feature_matrix: list/array of shape (n_samples, n_features)"""
        self.scaler = MinMaxScaler()
        self.scaler.fit(np.array(feature_matrix))
        return self

    def transform(self, feature_vector):
        """Scales a single vector (n_features,) or a batch (n_samples, n_features)."""
        if self.scaler is None:
            self.load()

        arr = np.array(feature_vector)
        if arr.ndim == 1:
            return self.scaler.transform(arr.reshape(1, -1))[0]
        else:
            return self.scaler.transform(arr)

    def fit_transform(self, feature_matrix):
        self.fit(feature_matrix)
        return self.scaler.transform(np.array(feature_matrix))

    def inverse_transform(self, scaled_vector):
        """Inverse-scales a single vector (n_features,) or a batch (n_samples, n_features)."""
        if self.scaler is None:
            self.load()

        arr = np.array(scaled_vector)
        if arr.ndim == 1:
            return self.scaler.inverse_transform(arr.reshape(1, -1))[0]
        else:
            return self.scaler.inverse_transform(arr)

    def save(self):
        if self.scaler is None:
            raise ValueError("Scaler is not fitted yet, nothing to save.")

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.scaler, self.model_path)

    def load(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"No fitted scaler found at {self.model_path}. "
                f"Run train_anomaly.py first."
            )
        self.scaler = joblib.load(self.model_path)
        return self
