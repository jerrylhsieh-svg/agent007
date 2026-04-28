from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import Any, Iterable

import joblib

from agent.learning_models.constants import TRANSACTION_ARTIFACT_PATH, UNKNOWN_LABEL
from agent.learning_models.transaction.merchant_rules import normalize_description, override_label
from agent.models.merchant_prediction import MerchantPrediction


class MerchantPredictor:

    def __init__(self, artifact_path: Path | None = None, threshold: float = 0.70) -> None:
        self.artifact_path = artifact_path or TRANSACTION_ARTIFACT_PATH
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

        label = override_label(description)
        if label is not None:
            return MerchantPrediction(
                merchant_type=label,
                confidence=1.0,
                source="override_rule",
                normalized_description=normalized,
                needs_review=False,
                predicted_label=label,
            )

        label, score = self._predict_with_model(normalized)
        needs_review = score < self.threshold

        return MerchantPrediction(
            merchant_type=UNKNOWN_LABEL if needs_review else label,
            confidence=score,
            source="model",
            normalized_description=normalized,
            needs_review=needs_review,
            predicted_label=label,
        )

    def predict_batch(self, descriptions: Iterable[str]) -> list[MerchantPrediction]:
        return [self.predict_one(description) for description in descriptions]

    def _predict_with_model(self, normalized_description: str) -> tuple[str, float]:
        probabilities = self.model.predict_proba([normalized_description])[0]
        classes = self.model.classes_

        best_index = int(probabilities.argmax())
        return str(classes[best_index]), float(probabilities[best_index])
