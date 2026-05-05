from __future__ import annotations

import re

from agent.db.data_classes.merchant_prediction import MerchantRule


OVERRIDE_RULES: list[MerchantRule] = [
    MerchantRule(
        re.compile(r"\b(uber\s*eats|ubereats|doordash|grubhub|seamless)\b", re.I),
        "Dining",
        "Food delivery should be Dining",
    ),
    MerchantRule(
        re.compile(r"\b(amazon|amzn)\b", re.I),
        "Merchandise",
        "Amazon purchases should be Merchandise.",
    ),
]


def override_transaction_label(description: str) -> str | None:
    for rule in OVERRIDE_RULES:
        if rule.pattern.search(description):
            return rule.label
    return None
