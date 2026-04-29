from __future__ import annotations

import re

from agent.models.merchant_prediction import MerchantRule


OVERRIDE_RULES: list[MerchantRule] = [
    MerchantRule(
        re.compile(r"\b(robinhood)\b", re.I),
        "investment",
        "stock investment",
    ),
]


def override_statement_label(description: str) -> str | None:
    for rule in OVERRIDE_RULES:
        if rule.pattern.search(description):
            return rule.label
    return None
