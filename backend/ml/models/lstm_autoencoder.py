import os
from typing import Optional, Tuple, Union
import numpy as np

# Prefer Keras / TensorFlow for .keras serialization; fall back gracefully if needed
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models
    HAS_KERAS = True
except ImportError:
    HAS_KERAS = False


def build_lstm_autoencoder(
    timesteps: int = 10,
    n_features: int = 11,
    latent_dim: int = 32,
    hidden_dim: int = 64,
    dropout: float = 0.2,
    learning_rate: float = 0.001,
):
    """
    Constructs and compiles a Keras LSTM Autoencoder for time-series anomaly detection.
    Encodes an input sequence of shape (timesteps, n_features) into a compressed latent bottleneck
    and reconstructs the expected normal baseline behavior.
    """
    if not HAS_KERAS:
        raise ImportError("TensorFlow / Keras is required to build the Keras LSTM Autoencoder.")

    # ── Encoder ─────────────────────────────────────────────────────────────
    encoder_inputs = keras.Input(shape=(timesteps, n_features), name="encoder_input")
    x = layers.LSTM(hidden_dim, activation="relu", return_sequences=True, dropout=dropout, name="enc_lstm_1")(encoder_inputs)
    latent = layers.LSTM(latent_dim, activation="relu", return_sequences=False, name="enc_latent")(x)

    # ── Bottleneck Repeat ───────────────────────────────────────────────────
    x = layers.RepeatVector(timesteps, name="bottleneck_repeat")(latent)

    # ── Decoder ─────────────────────────────────────────────────────────────
    x = layers.LSTM(latent_dim, activation="relu", return_sequences=True, name="dec_lstm_1")(x)
    x = layers.LSTM(hidden_dim, activation="relu", return_sequences=True, dropout=dropout, name="dec_lstm_2")(x)
    decoder_outputs = layers.TimeDistributed(layers.Dense(n_features, activation="sigmoid"), name="reconstruction")(x)

    autoencoder = models.Model(inputs=encoder_inputs, outputs=decoder_outputs, name="lstm_autoencoder")
    optimizer = keras.optimizers.Adam(learning_rate=learning_rate)
    autoencoder.compile(optimizer=optimizer, loss="mse", metrics=["mae"])

    return autoencoder


class LSTMAutoencoder:
    """
    Wrapper for the LSTM Autoencoder neural network model.
    Provides inference, reconstruction error calculation, and checkpoint persistence (.keras).
    """

    def __init__(
        self,
        timesteps: int = 10,
        n_features: int = 11,
        latent_dim: int = 32,
        hidden_dim: int = 64,
        model_path: str = "backend/ml/saved_models/lstm_autoencoder.keras",
    ):
        self.timesteps = timesteps
        self.n_features = n_features
        self.latent_dim = latent_dim
        self.hidden_dim = hidden_dim
        self.model_path = model_path
        self.model = None

        self._init_model()

    def _init_model(self) -> None:
        """Initializes or loads model from file."""
        if os.path.exists(self.model_path) and HAS_KERAS:
            try:
                self.load(self.model_path)
            except Exception as e:
                print(f"[LSTMAutoencoder] Warning: Could not load model from {self.model_path}: {e}")
                self.model = build_lstm_autoencoder(
                    timesteps=self.timesteps,
                    n_features=self.n_features,
                    latent_dim=self.latent_dim,
                    hidden_dim=self.hidden_dim,
                )
        elif HAS_KERAS:
            self.model = build_lstm_autoencoder(
                timesteps=self.timesteps,
                n_features=self.n_features,
                latent_dim=self.latent_dim,
                hidden_dim=self.hidden_dim,
            )

    def reconstruct(self, sequence: np.ndarray) -> np.ndarray:
        """
        Reconstructs a batch of 3D sequences of shape (N, timesteps, n_features).
        """
        seq = np.asarray(sequence, dtype=np.float32)
        if seq.ndim == 2:
            seq = np.expand_dims(seq, axis=0)

        if self.model is not None:
            return self.model.predict(seq, verbose=0)
        else:
            # Fallback identity reconstruction if weights not present
            return seq

    def compute_reconstruction_error(
        self,
        sequence: np.ndarray,
        reduction: str = "mean",
    ) -> Union[float, np.ndarray]:
        """
        Computes reconstruction MSE error.
        - 'mean': Returns scalar mean error.
        - 'sample': Returns (batch_size,) error per sample.
        - 'feature': Returns (n_features,) error per feature.
        - 'none': Returns raw (batch_size, timesteps, n_features) squared errors.
        """
        seq = np.asarray(sequence, dtype=np.float32)
        if seq.ndim == 2:
            seq = np.expand_dims(seq, axis=0)

        reconstructed = self.reconstruct(seq)
        squared_err = (seq - reconstructed) ** 2

        if reduction == "mean":
            return float(np.mean(squared_err))
        elif reduction == "sample":
            return np.mean(squared_err, axis=(1, 2))
        elif reduction == "feature":
            return np.mean(squared_err, axis=(0, 1))
        elif reduction == "none":
            return squared_err
        else:
            raise ValueError(f"Unknown reduction: {reduction}")

    def save(self, filepath: Optional[str] = None) -> None:
        """Saves Keras model to disk (.keras format)."""
        target = filepath or self.model_path
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        if self.model is not None and HAS_KERAS:
            self.model.save(target)
            print(f"[LSTMAutoencoder] Model saved to {target}")

    def load(self, filepath: Optional[str] = None) -> "LSTMAutoencoder":
        """Loads Keras model from disk (.keras format)."""
        target = filepath or self.model_path
        if not os.path.exists(target):
            raise FileNotFoundError(f"Model file not found: {target}")

        if HAS_KERAS:
            self.model = keras.models.load_model(target)
            self.model_path = target
            print(f"[LSTMAutoencoder] Model successfully loaded from {target}")
        return self
