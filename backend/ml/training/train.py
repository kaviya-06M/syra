import argparse
import os
from typing import Any, Dict, Optional

import numpy as np

try:
    import tensorflow as tf
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
    from backend.ml.models.lstm_autoencoder import LSTMAutoencoder, build_lstm_autoencoder
    from backend.ml.training.dataset import TelemetryDataset, prepare_data_splits
    from backend.ml.utils.threshold import AnomalyThreshold, compute_threshold_stats
    from backend.preprocessing.feature_engineering import FeatureEngineer
except ImportError:
    from ..models.lstm_autoencoder import LSTMAutoencoder, build_lstm_autoencoder
    from .dataset import TelemetryDataset, prepare_data_splits
    from ..utils.threshold import AnomalyThreshold, compute_threshold_stats
    from ...preprocessing.feature_engineering import FeatureEngineer


def train_lstm_autoencoder(
    epochs: int = 40,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    sequence_length: int = 10,
    saved_dir: str = "backend/ml/saved_models",
    db_session: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Executes the training workflow for the LSTM Autoencoder.
    Trains on normal telemetry, computes the reconstruction anomaly threshold,
    and persists lstm_autoencoder.keras, feature_scaler.pkl, and threshold.json.
    """
    os.makedirs(saved_dir, exist_ok=True)
    model_path = os.path.join(saved_dir, "lstm_autoencoder.keras")
    scaler_path = os.path.join(saved_dir, "feature_scaler.pkl")
    threshold_path = os.path.join(saved_dir, "threshold.json")

    dataset_builder = TelemetryDataset(
        sequence_length=sequence_length,
        scaler_path=scaler_path,
    )

    if db_session is not None:
        sequences, scaler = dataset_builder.from_database(db_session)
    else:
        sequences, scaler = dataset_builder.from_synthetic(num_samples=2500)

    train_data, val_data = prepare_data_splits(sequences, train_ratio=0.8)
    print(f"[Train] Prepared sequences — Train: {train_data.shape}, Val: {val_data.shape}")

    n_features = train_data.shape[2]
    model = build_lstm_autoencoder(
        timesteps=sequence_length,
        n_features=n_features,
        latent_dim=32,
        hidden_dim=64,
        dropout=0.2,
        learning_rate=learning_rate,
    )

    callbacks = [
        EarlyStopping(
            monitor="val_loss",
            patience=8,
            mode="min",
            restore_best_weights=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=4,
            min_lr=1e-5,
            verbose=1,
        ),
        ModelCheckpoint(
            filepath=model_path,
            monitor="val_loss",
            save_best_only=True,
            verbose=1,
        ),
    ]

    print(f"[Train] Training LSTM Autoencoder for up to {epochs} epochs...")
    history = model.fit(
        train_data,
        train_data,
        epochs=epochs,
        batch_size=batch_size,
        validation_data=(val_data, val_data),
        callbacks=callbacks,
        verbose=1,
    )

    # Save final model state
    model.save(model_path)
    print(f"[Train] Saved model checkpoint to {model_path}")

    # Evaluate validation reconstruction errors to establish threshold
    val_preds = model.predict(val_data, verbose=0)
    val_mse_per_sample = np.mean((val_data - val_preds) ** 2, axis=(1, 2))
    threshold_stats = compute_threshold_stats(val_mse_per_sample.tolist(), percentile=99.0, std_multiplier=3.0)

    threshold_manager = AnomalyThreshold(filepath=threshold_path)
    threshold_manager.save(threshold_stats)

    print(f"[Train] Saved threshold stats to {threshold_path}: {threshold_stats}")

    return {
        "model_path": model_path,
        "scaler_path": scaler_path,
        "threshold_path": threshold_path,
        "threshold_stats": threshold_stats,
        "final_val_loss": float(history.history["val_loss"][-1]),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train SYRA Keras LSTM Autoencoder")
    parser.add_argument("--epochs", type=int, default=30, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--saved-dir", type=str, default="backend/ml/saved_models", help="Artifacts directory")
    args = parser.parse_args()

    train_lstm_autoencoder(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        saved_dir=args.saved_dir,
    )
