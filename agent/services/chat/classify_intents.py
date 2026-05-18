import json
import requests

from agent.db.data_classes.chat import RouteDecision, Intent
from agent.services.constants_and_dependencies import MODEL, OLLAMA_HOST



ROUTER_SYSTEM_PROMPT = """
You are an intent classifier for a personal finance AI assistant.

Choose exactly one intent from this list:

- analyze_transactions: user wants spending summaries, charts, category totals, merchant analysis, or financial insights
- extract_pdf: user wants to upload/extract/parse a PDF statement
- train_model: user wants to train or retrain the transaction labeling model
- repredict_records: user wants to relabel, predict, classify, or re-run predictions on existing records
- show_unlabeled: user wants to see transactions that need manual labeling
- label_records: user wants to assign labels/categories to transactions
- general_chat: general question, explanation, or coding help unrelated to app actions
- unknown: unclear or unsupported request

Return only valid JSON with this shape:

{
  "intent": "...",
  "confidence": 0.0,
  "reason": "...",
  "needs_db": true,
  "extracted_args": {}
}

Rules:
- Do not invent unsupported intents.
- Use train_model only when the user clearly wants model training/retraining.
- Use repredict_records when the user wants predictions or labels regenerated.
- Use extract_pdf only when the user refers to uploading, parsing, reading, or extracting from a PDF.
- Use analyze_transactions for spending analysis, summaries, trends, balances, or reports.
- If unclear, use unknown with low confidence.
"""


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
"""

    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": MODEL,
            "prompt": ROUTER_SYSTEM_PROMPT + "\n\n" + prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0,
            },
        },
        timeout=30,
    )
    response.raise_for_status()

    raw = response.json()["response"]

    try:
        data = json.loads(raw)
        return RouteDecision(**data)
    except Exception:
        return RouteDecision(
            intent=Intent.UNKNOWN,
            confidence=0.0,
            reason="Failed to parse router response.",
            needs_db=False,
            extracted_args={},
        )