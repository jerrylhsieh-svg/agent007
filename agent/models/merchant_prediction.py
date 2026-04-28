
from dataclasses import dataclass


@dataclass(frozen=True)
class MerchantPrediction:
    merchant_type: str
    confidence: float
    source: str
    normalized_description: str
    needs_review: bool
    predicted_label: str