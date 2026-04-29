from __future__ import annotations

import re

from agent.models.merchant_prediction import MerchantRule


OVERRIDE_RULES: list[MerchantRule] = [
    MerchantRule(
        re.compile(r"\b(uber\s*one|uber\s*pass)\b", re.I),
        "subscription_membership",
        "Uber membership should not be classified as rideshare.",
    ),
    MerchantRule(
        re.compile(r"\b(uber\s*eats|ubereats|doordash|grubhub|seamless)\b", re.I),
        "food_delivery",
        "Food delivery should be separated from restaurants.",
    ),
    MerchantRule(
        re.compile(r"\b(uber\s*trip|uber\*?\s*trip|lyft)\b", re.I),
        "transportation",
        "Rideshare should be separated from Uber Eats and Uber One.",
    ),
    MerchantRule(
        re.compile(r"\b(amazon\s*prime|amzn\s*prime|prime\s*membership)\b", re.I),
        "subscription_membership",
        "Amazon subscription should be separated from Amazon shopping.",
    ),
    MerchantRule(
        re.compile(r"\b(amazon|amzn)\b", re.I),
        "amazon",
        "Amazon purchases should have their own category.",
    ),
]


def override_transaction_label(description: str) -> str | None:
    for rule in OVERRIDE_RULES:
        if rule.pattern.search(description):
            return rule.label
    return None
