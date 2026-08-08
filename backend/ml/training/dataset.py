from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    from sqlalchemy.orm import Session
    from backend.database.crud import get_all_metrics
    from backend.preprocessing.cleaner import DataCleaner
    from backend.preprocessing.feature_engineering import FeatureEngineer
    from backend.preprocessing.scaler import FeatureScaler
    from backend.preprocessing.sequence_builder import SequenceBuilder
except ImportError:
    from ...database.crud import get_all_metrics
    from ...preprocessing.cleaner import DataCleaner
    from ...preprocessing.feature_engineering import FeatureEngineer
    from ...preprocessing.scaler import FeatureScaler
    from ...preprocessing.sequence_builder import SequenceBuilder


class TelemetryDataset:
    """
    Constructs and manages sliding-window sequence datasets for training
    and evaluating the LSTM Autoencoder.
    """

    def __init__(
        self,
        sequence_length: int = 10,
        scaler_path: str = "backend/ml/saved_models/feature_scaler.pkl",
    ):
        self.sequence_length = sequence_length
        self.scaler_path = scaler_path
        self.cleaner = DataCleaner()
        self.engineer = FeatureEngineer()
        self.scaler = FeatureScaler(model_path=scaler_path)
        self.seq_builder = SequenceBuilder(sequence_length=sequence_length)

    def from_synthetic(self, num_samples: int = 2000) -> Tuple[np.ndarray, FeatureScaler]:
        """
        Generates synthetic normal baseline telemetry for initial training.
        """
        np.random.seed(42)
        cpu = np.random.uniform(0.10, 0.45, size=(num_samples, 1))
        mem = np.random.uniform(0.25, 0.55, size=(num_samples, 1))
        disk = np.random.uniform(0.20, 0.40, size=(num_samples, 1))
        net_tx = np.random.uniform(0.01, 0.20, size=(num_samples, 1))
        net_rx = np.random.uniform(0.01, 0.25, size=(num_samples, 1))
        pkt_tx = np.random.uniform(0.01, 0.15, size=(num_samples, 1))
        pkt_rx = np.random.uniform(0.01, 0.15, size=(num_samples, 1))
        proc_cnt = np.random.uniform(0.10, 0.30, size=(num_samples, 1))
        top_cpu = cpu * np.random.uniform(0.40, 0.80, size=(num_samples, 1))
        top_mem = mem * np.random.uniform(0.40, 0.70, size=(num_samples, 1))
        win_evt = np.zeros((num_samples, 1))

        matrix = np.hstack([
            cpu, mem, disk, net_tx, net_rx, pkt_tx, pkt_rx,
            proc_cnt, top_cpu, top_mem, win_evt
        ]).astype(np.float32)

        scaled = self.scaler.fit_transform(matrix)
        self.scaler.save()

        sequences = self.seq_builder.build(scaled)
        return sequences, self.scaler

    def from_database(
        self,
        db_session: Session,
        limit: int = 10000,
    ) -> Tuple[np.ndarray, FeatureScaler]:
        """
        Fetches historical telemetry snapshots from SQLite and prepares 3D training sequences.
        """
        metrics = get_all_metrics(db_session, limit=limit)
        if not metrics or len(metrics) < self.sequence_length:
            print("[TelemetryDataset] Database contains insufficient data. Falling back to baseline synthetic telemetry.")
            return self.from_synthetic(num_samples=2000)

        feature_matrix = []
        for m in metrics:
            vec = [
                float(m.cpu_usage or 0.0),
                float(m.memory_usage or 0.0),
                float(m.disk_usage or 0.0),
                float(m.network_usage or 0.0),
                0.0,
                0.0,
                0.0,
                1.0 if m.process_name else 0.0,
                float(m.cpu_usage or 0.0),
                float(m.memory_usage or 0.0),
                0.0,
            ]
            feature_matrix.append(vec)

        matrix = np.asarray(feature_matrix, dtype=np.float32)
        scaled = self.scaler.fit_transform(matrix)
        self.scaler.save()

        sequences = self.seq_builder.build(scaled)
        return sequences, self.scaler

    def from_raw_events(
        self,
        events: List[Dict[str, Any]],
    ) -> Tuple[np.ndarray, FeatureScaler]:
        """
        Cleans and transforms raw JSON snapshots from agent event generator.
        """
        cleaned = [self.cleaner.clean(e) for e in events]
        features = [self.engineer.transform(e) for e in cleaned]
        matrix = np.asarray(features, dtype=np.float32)

        scaled = self.scaler.fit_transform(matrix)
        self.scaler.save()

        sequences = self.seq_builder.build(scaled)
        return sequences, self.scaler


def prepare_data_splits(
    sequences: np.ndarray,
    train_ratio: float = 0.8,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Performs chronological split to avoid data leakage in sequential time-series.
    """
    total = len(sequences)
    if total == 0:
        raise ValueError("Cannot split empty sequence array.")

    split_idx = int(total * train_ratio)
    train_data = sequences[:split_idx]
    val_data = sequences[split_idx:]

    return train_data, val_data
