"""Train a root-cause classifier from verified incident feedback only."""

import argparse
import json
import os
import sys
from collections import Counter

import joblib
from sklearn.ensemble import RandomForestClassifier

_WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, _WORKSPACE_ROOT)

from backend.database.database import SessionLocal
from backend.ml.root_cause.dataset import FEATURE_NAMES, build_verified_dataset


def train_root_cause_model(db_session, model_path: str = "backend/ml/saved_models/root_cause_classifier.joblib") -> dict:
    features, labels = build_verified_dataset(db_session)
    class_counts = Counter(labels.tolist())
    if len(features) < 10 or len(class_counts) < 2:
        raise ValueError(
            "Need at least 10 verified, remediated incidents across at least two root-cause labels. "
            f"Found {len(features)} incidents and {len(class_counts)} labels."
        )

    model = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42,
        min_samples_leaf=2,
    )
    model.fit(features, labels)
    os.makedirs(os.path.dirname(os.path.abspath(model_path)), exist_ok=True)
    joblib.dump(model, model_path)
    return {
        "model_path": model_path,
        "training_incidents": int(len(features)),
        "class_counts": dict(class_counts),
        "feature_names": FEATURE_NAMES,
        "classes": model.classes_.tolist(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train SYRA root-cause classifier from verified incidents")
    parser.add_argument("--model-path", default="backend/ml/saved_models/root_cause_classifier.joblib")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        print(json.dumps(train_root_cause_model(db, args.model_path), indent=2))
    finally:
        db.close()
