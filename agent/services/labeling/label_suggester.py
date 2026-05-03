import json
import re

from agent.models.label import LabelSuggested, UnlabeledRecord
from agent.services.call_model import call_model
from agent.services.constants_and_dependencies import ALLOWED_TRANSACTION_LABELS
from agent.services.helper import safe_float


class LabelSuggester:
    def __init__(self, allowed_labels: list[str] | None = None):
        self.allowed_labels = allowed_labels or ALLOWED_TRANSACTION_LABELS

    def suggest_one_label(
        self,
        unlabel_reocrd: UnlabeledRecord,
    ) -> LabelSuggested:
        prompt = self._build_prompt(
            description=unlabel_reocrd.description,
            normalized_description=unlabel_reocrd.normalized_description,
            amount=unlabel_reocrd.total_amount_impact,
            similar_count=unlabel_reocrd.similar_count,
            predicted_label=unlabel_reocrd.predicted_label,
            confidence=unlabel_reocrd.confidence,
        )

        raw_response = call_model(prompt, [])
        data = self._parse_json(raw_response)

        label = str(data.get("suggested_label", "needs_manual_review")).strip()

        if label not in self.allowed_labels:
            label = "needs_manual_review"

        confidence = safe_float(data.get("confidence", 0.0))

        return LabelSuggested(
            suggested_label=label,
            confidence=max(0.0, min(confidence, 1.0)),
            reason=str(data.get("reason", "")).strip(),
        )

    def _build_prompt(
        self,
        description: str,
        normalized_description: str,
        amount: float | None,
        similar_count: int,
        predicted_label: str,
        confidence: float,
    ) -> str:
        labels = "\n".join(f"- {label}" for label in self.allowed_labels)

        return f"""
You are helping classify personal finance transactions.

Choose exactly one label from this allowed list:

{labels}

Transaction:
- Description: {description}
- Normalized description: {normalized_description}
- Amount: {amount}
- Similar transaction count: {similar_count}
- ML predicted label: {predicted_label}
- ML confidence: {confidence}

Rules:
- Use "needs_manual_review" if the transaction is ambiguous.
- Do not invent new labels.
- Return only valid JSON.
- Confidence must be between 0 and 1.
- Keep reason short.

Return JSON in this format:
{{
  "suggested_label": "restaurant",
  "confidence": 0.85,
  "reason": "Coffee shop purchase."
}}
""".strip()

    def _parse_json(self, raw_response: str) -> dict:
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", raw_response, flags=re.DOTALL)
        if not match:
            return {}

        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
