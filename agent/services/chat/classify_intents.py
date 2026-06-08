import json
import requests

from agent.db.data_classes.chat import RouteDecision
from agent.db.data_classes.intents import Intents
from agent.services.constants_and_dependencies import MODEL, OLLAMA_HOST



def build_intent_catalog() -> str:
    sections = []

    for intent in Intents:
        examples = "\n".join(f"    - {example}" for example in intent.examples)

        sections.append(
            f"""
- {intent.value}
  Description: {intent.description}
  Needs DB: {str(intent.needs_db).lower()}
  Examples:
{examples}
""".strip()
        )

    return "\n\n".join(sections)

def build_router_system_prompt() -> str:
    allowed_values = ", ".join(f'"{intent.value}"' for intent in Intents)

    return f"""
You are an intent classifier for a personal finance AI assistant.

Your job is to classify the user's message into exactly one allowed intent.

Allowed intents:
{build_intent_catalog()}

Return only valid JSON with exactly this shape:

{{
  "intent": "one_allowed_intent_value",
  "confidence": 0.0,
  "reason": "brief explanation",
  "needs_db": false,
  "extracted_args": {{}}
}}

Rules:
- The intent must be one of: {allowed_values}
- Never invent a new intent.
- Choose the intent whose description and examples best match the user message.
- If multiple intents seem possible, choose the most specific app action.
- Use general_chat only when the user is asking for explanation, coding help, or normal conversation.
- Use unknown when the message is too unclear or unsupported.
- Set needs_db to the exact Needs DB value from the selected intent.
- Keep confidence between 0.0 and 1.0.
- Use 0.9+ for explicit requests.
- Use 0.6-0.8 for likely but somewhat ambiguous requests.
- Use below 0.5 for unclear requests.
- extracted_args must be an object.
- Include extracted_args only when obvious from the message.
""".strip()


def classify_intent(message: str, history: list[dict] | None = None) -> RouteDecision:
    history_text = ""
    if history:
        recent = history[-5:]
        history_text = "\n".join(
            f"{item.get('role', 'user')}: {item.get('content', '')}"
            for item in recent
        )

    prompt = f"""
Conversation history:
{history_text}

User message:
{message}

Classify the user's intent.
""".strip()

    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": MODEL,
            "prompt": build_router_system_prompt() + "\n\n" + prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0,
            },
        },
        timeout=300,
    )

    response.raise_for_status()
    raw = response.json()["response"]

    try:
        data = json.loads(raw)
        intent = parse_intent(data.get("intent"))

        return RouteDecision(
            intent=intent,
            confidence=float(data.get("confidence", 0.0)),
            reason=data.get("reason", ""),
            needs_db=intent.needs_db,
            extracted_args=data.get("extracted_args") or {},
        )

    except Exception:
        return RouteDecision(
            intent=Intents.UNKNOWN,
            confidence=0.0,
            reason="Failed to parse router response.",
            needs_db=Intents.UNKNOWN.needs_db,
            extracted_args={},
        )
    
def parse_intent(value: object) -> Intents:
    if not isinstance(value, str):
        return Intents.UNKNOWN

    for intent in Intents:
        if intent.value == value:
            return intent

    return Intents.UNKNOWN