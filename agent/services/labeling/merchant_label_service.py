from dataclasses import asdict
from typing import Any

from agent.ml.merchant_predictor import MerchantPredictor


class MerchantLabelService:
    def __init__(self, predictor: MerchantPredictor | None = None) -> None:
        self.predictor = predictor or MerchantPredictor()

    def label_one(self, description: str) -> dict[str, Any]:
        prediction = self.predictor.predict_one(description)
        return asdict(prediction)

    def label_many(self, descriptions: list[str]) -> list[dict[str, Any]]:
        predictions = self.predictor.predict_batch(descriptions)
        return [asdict(prediction) for prediction in predictions]