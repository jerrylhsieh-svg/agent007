from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MerchantRule:
    pattern: re.Pattern[str]
    label: str
    reason: str

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


def normalize_description(text: str) -> str:
    normalized = text.lower()
    normalized = normalized.replace("*", " ")
    normalized = re.sub(r"\d{3,}", " ", normalized)
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def override_label(description: str) -> str | None:
    normalized = normalize_description(description)
    for rule in OVERRIDE_RULES:
        if rule.pattern.search(normalized):
            return rule.label
    return None
