from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

import joblib

from agent.ml.merchant_rules import normalize_description, rule_based_label


ARTIFACT_PATH = Path(__file__).resolve().parent / "artifacts" / "merchant_classifier.joblib"


@dataclass
class MerchantPrediction:
    merchant_type: str
    confidence: float
    source: str
    normalized_description: str


class MerchantPredictor:
    def __init__(self, artifact_path: Path | None = None, threshold: float = 0.70) -> None:
        self.artifact_path = artifact_path or ARTIFACT_PATH
        self.threshold = threshold

    @cached_property
    def model(self) -> Any:
        if not self.artifact_path.exists():
            raise FileNotFoundError(
                f"Model artifact not found at {self.artifact_path}. Train the model first."
            )
        return joblib.load(self.artifact_path)

    def predict_one(self, description: str) -> MerchantPrediction:
        normalized = normalize_description(description)

        rule_label = rule_based_label(description)
        if rule_label:
            return MerchantPrediction(
                merchant_type=rule_label,
                confidence=1.0,
                source="rule",
                normalized_description=normalized,
            )

        probabilities = self.model.predict_proba([normalized])[0]
        classes = self.model.classes_

        best_index = int(probabilities.argmax())
        best_label = str(classes[best_index])
        best_score = float(probabilities[best_index])

        if best_score < self.threshold:
            best_label = "unknown"

        return MerchantPrediction(
            merchant_type=best_label,
            confidence=best_score,
            source="model",
            normalized_description=normalized,
        )

    def predict_batch(self, descriptions: list[str]) -> list[MerchantPrediction]:
        return [self.predict_one(description) for description in descriptions]