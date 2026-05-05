
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class MerchantPrediction:
    merchant_type: str
    confidence: float
    source: str
    normalized_description: str
    needs_review: bool
    predicted_label: str

@dataclass(frozen=True)
class MerchantRule:
    pattern: re.Pattern[str]
    label: str
    reason: str