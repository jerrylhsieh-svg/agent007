import re
from typing import Optional

RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(robinhood|etrade|fidelity|vanguard)\b", re.I), "investment"),
    (re.compile(r"\b(zelle|venmo|cash app|cashapp)\b", re.I), "transfer"),
    (re.compile(r"\b(atm|cash withdrawal|withdraw)\b", re.I), "cash_withdrawal"),
    (re.compile(r"\b(uber|lyft)\b", re.I), "transportation"),
    (re.compile(r"\b(whole ?foods|wholefds|trader joe'?s|costco|aldi|kroger)\b", re.I), "groceries"),
    (re.compile(r"\b(starbucks|mcdonald'?s|chipotle|doordash|ubereats)\b", re.I), "restaurant"),
    (re.compile(r"\b(netflix|spotify|apple\.com\/bill)\b", re.I), "subscription"),
    (re.compile(r"\b(amazon|amzn|paypal|square|sq)\b", re.I), "shopping"),
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