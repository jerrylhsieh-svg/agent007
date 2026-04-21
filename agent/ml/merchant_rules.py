import re
from typing import Optional

RULES: list[tuple[re.Pattern[str], str]] = [
    # transportation
    (re.compile(r"\b(uber trip|uber\*? ?trip|lyft)\b", re.I), "transportation"),

    # gas
    (re.compile(r"\b(shell|exxon|mobil|chevron|bp|sunoco)\b", re.I), "gas"),

    # groceries
    (re.compile(r"\b(whole ?foods|wholefds|trader joe'?s|costco|aldi|kroger)\b", re.I), "groceries"),

    # food delivery first, before generic restaurant
    (re.compile(r"\b(doordash|ubereats|uber eats|grubhub|seamless)\b", re.I), "restaurant"),

    # restaurants / coffee
    (re.compile(r"\b(starbucks|mcdonald'?s|chipotle|sweetgreen|coffee|tst\*?)\b", re.I), "restaurant"),

    # subscriptions / digital services
    (re.compile(r"\b(netflix|spotify|youtube ?premium|apple\.com/bill|apple\.com\/bill|uber ?one)\b", re.I), "subscription"),

    # shopping / retail / marketplaces
    (re.compile(r"\b(amazon|amzn|paypal|square)\b", re.I), "shopping"),
]


def normalize_description(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\d{3,}", " ", text)         
    text = re.sub(r"[^a-z0-9\s*]", " ", text)  
    text = text.replace("*", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def rule_based_label(description: str) -> Optional[str]:
    normalized = normalize_description(description)
    for pattern, label in RULES:
        if pattern.search(normalized):
            return label
    return None