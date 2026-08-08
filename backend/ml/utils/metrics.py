from typing import Dict, List, Optional, Tuple, Union
import numpy as np


def compute_reconstruction_metrics(
    actual: np.ndarray,
    reconstructed: np.ndarray,
) -> Dict[str, float]:
    """
    Calculates reconstruction metrics across true and reconstructed sequences.
    """
    act = np.asarray(actual, dtype=np.float32)
    rec = np.asarray(reconstructed, dtype=np.float32)

    diff = act - rec
    mse = float(np.mean(diff ** 2))
    mae = float(np.mean(np.abs(diff)))
    rmse = float(np.sqrt(mse))
    max_err = float(np.max(np.abs(diff)))

    return {
        "mse": round(mse, 6),
        "mae": round(mae, 6),
        "rmse": round(rmse, 6),
        "max_error": round(max_err, 6),
    }


def compute_feature_contributions(
    actual: np.ndarray,
    reconstructed: np.ndarray,
    feature_names: Optional[List[str]] = None,
) -> List[Dict[str, Union[str, float]]]:
    """
    Computes per-feature reconstruction error contributions to isolate
    the root cause of an anomaly (e.g., CPU burst, memory leak, network flood).
    """
    act = np.asarray(actual, dtype=np.float32)
    rec = np.asarray(reconstructed, dtype=np.float32)

    if act.ndim == 2:  # (seq_len, num_features)
        feature_errors = np.mean((act - rec) ** 2, axis=0)
    elif act.ndim == 3:  # (batch_size, seq_len, num_features)
        feature_errors = np.mean((act - rec) ** 2, axis=(0, 1))
    else:
        raise ValueError(f"Expected 2D or 3D array, got shape: {act.shape}")

    num_features = len(feature_errors)
    if feature_names is None or len(feature_names) != num_features:
        feature_names = [f"feature_{i}" for i in range(num_features)]

    total_error = float(np.sum(feature_errors))
    contributions = []

    for name, err in zip(feature_names, feature_errors):
        err_val = float(err)
        pct = (err_val / total_error * 100.0) if total_error > 0 else 0.0
        contributions.append({
            "feature": name,
            "error": round(err_val, 6),
            "contribution_percent": round(pct, 2),
        })

    # Sort descending by error impact
    contributions.sort(key=lambda x: x["error"], reverse=True)
    return contributions


def compute_anomaly_score(
    reconstruction_error: float,
    threshold: float,
) -> float:
    """
    Normalizes reconstruction error against the anomaly threshold into a continuous score.
    """
    safe_thresh = max(threshold, 1e-6)
    score = float(reconstruction_error / safe_thresh)
    return round(score, 4)
