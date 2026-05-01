from typing import Iterable

from agent.services.constants_and_dependencies import SAVE_TRIGGERS

def normalize(text: str) -> str:
    return text.strip().lower()

def contains_any_trigger(message: str, triggers: Iterable[str]) -> bool:
    msg = normalize(message)
    return any(trigger in msg for trigger in triggers)

def should_start_file_flow(message: str) -> bool:
    msg = normalize(message)
    return any(trigger in msg for trigger in SAVE_TRIGGERS)
