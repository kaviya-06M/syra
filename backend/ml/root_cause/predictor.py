"""Loads the verified-incident classifier and returns explainable probabilities."""

import os
from typing import Any

import joblib

from .dataset import FEATURE_NAMES, extract_features


class RootCausePredictor:
    def __init__(self, model_path: str = "backend/ml/saved_models/root_cause_classifier.joblib"):
        self.model_path = model_path
        self.model = None
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
            except Exception as exc:
                print(f"[RootCausePredictor] Model unavailable: {exc}")

    @property
    def available(self) -> bool:
        return self.model is not None

    def predict(self, event_data: dict[str, Any], anomaly_info: dict[str, Any] | None, matched_rules: list[dict]) -> dict[str, Any]:
        if not self.available:
            return {"available": False, "root_cause": None, "confidence": 0.0, "probabilities": {}}

        vector = extract_features(event_data, anomaly_info, matched_rules)
        probabilities = self.model.predict_proba([vector])[0]
        labels = self.model.classes_
        scores = {str(label): round(float(score), 4) for label, score in zip(labels, probabilities)}
        root_cause = max(scores, key=scores.get)
        return {
            "available": True,
            "root_cause": root_cause,
            "confidence": scores[root_cause],
            "probabilities": scores,
            "feature_names": FEATURE_NAMES,
        }
