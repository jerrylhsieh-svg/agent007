import json
import requests

from agent.db.data_classes.chat import RouteDecision, Intent
from agent.services.constants_and_dependencies import MODEL, OLLAMA_HOST



ROUTER_SYSTEM_PROMPT = """
You are an intent classifier for a personal finance AI assistant.

Your job is to choose exactly one intent from the allowed enum values below.

Allowed intents:

- analyze_card_transactions
  User wants to analyze credit card transactions, card spending, merchants, categories,
  transaction summaries, spending charts, or card-based financial insights.

- analyze_bank_statements
  User wants to analyze bank statement records, deposits, withdrawals, cash flow,
  balances, income/outflow summaries, or statement-based financial insights.

- train_card_model
  User wants to train or retrain the model used to label credit card transactions.

- train_statement_model
  User wants to train or retrain the model used to label bank statement records.

- repredict_card_records
  User wants to rerun predictions, regenerate labels, classify again, or relabel
  existing credit card transaction records using the trained card model.

- repredict_statement_records
  User wants to rerun predictions, regenerate labels, classify again, or relabel
  existing bank statement records using the trained statement model.

- label_records
  User wants to manually assign, update, correct, or save labels/categories for
  one or more records.

- general_chat
  User is asking a general question, coding question, explanation, or anything
  unrelated to taking an app action.

- unknown
  The request is unclear, unsupported, or does not provide enough information to
  choose a safe intent.

Return only valid JSON with exactly this shape:

{
  "intent": "one_allowed_intent_value",
  "confidence": 0.0,
  "reason": "brief explanation",
  "needs_db": false,
  "extracted_args": {}
}

Classification rules:

1. Only return one of the allowed intent string values. Never invent new intents.

2. Use card intents when the user mentions:
   - credit card
   - card transactions
   - card spending
   - merchants
   - transaction categories
   - purchases

3. Use statement intents when the user mentions:
   - bank statement
   - statement records
   - deposits
   - withdrawals
   - income
   - cash flow
   - balance
   - bank account activity

4. If the user asks to analyze data but does not clearly specify card transactions
   or bank statements:
   - choose analyze_card_transactions if the wording focuses on spending,
     merchants, purchases, or categories.
   - choose analyze_bank_statements if the wording focuses on deposits,
     withdrawals, cash flow, or balances.
   - choose unknown if there is not enough context.

5. Use train_card_model only when the user clearly wants to train or retrain the
   credit card transaction labeling model.

6. Use train_statement_model only when the user clearly wants to train or retrain
   the bank statement labeling model.

7. Use repredict_card_records when the user wants predictions or labels regenerated
   for existing credit card transaction records.

8. Use repredict_statement_records when the user wants predictions or labels
   regenerated for existing bank statement records.

9. Use show_unlabeled when the user asks to see records needing manual labeling,
   unknown records, low-confidence predictions, or unlabeled records.

10. Use label_records when the user provides or wants to assign labels/categories
    to records.

11. Use general_chat for explanations, implementation help, debugging, or general
    conversation that should not trigger a finance app workflow.

12. If the user asks about uploading, parsing, extracting, or reading a PDF, classify
    based on the type of file if clear:
    - credit card PDF -> analyze_card_transactions
    - bank statement PDF -> analyze_bank_statements
    If the user only says "upload PDF" or "extract PDF" without enough context,
    use unknown.

13. Set needs_db:
    - true for analyze_card_transactions
    - true for analyze_bank_statements
    - true for train_card_model
    - true for train_statement_model
    - true for repredict_card_records
    - true for repredict_statement_records
    - true for show_unlabeled
    - true for label_records
    - false for general_chat
    - false for unknown

14. Keep confidence between 0.0 and 1.0.
    - 0.9+ for explicit requests
    - 0.6-0.8 for likely but slightly ambiguous requests
    - below 0.5 for unclear requests

15. extracted_args should be an object. Include useful fields only when obvious,
    such as:
    {
      "record_type": "card"
    }
    or
    {
      "record_type": "statement"
    }
    Otherwise return {}.
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