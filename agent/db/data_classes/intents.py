from enum import Enum


class Intents(str, Enum):
    description: str
    needs_db: bool
    examples: list[str]

    QUERY_TRANSACTIONS = (
        "query_transactions",
        "User wants to ask questions about existing transaction data using the database.",
        True,
        [
            "What are my top 3 transactions?",
            "Show average spending by category.",
            "Which merchant did I spend the most on?",
            "Show my recent transactions.",
        ],
    )

    ANALYZE_CARD_TRANSACTIONS = (
        "analyze_card_transactions",
        "User wants a summary or analysis of uploaded/imported credit card transactions.",
        True,
        [
            "Analyze my credit card transactions.",
            "Summarize my card spending.",
            "Show spending by merchant from my card file.",
        ],
    )

    ANALYZE_BANK_STATEMENTS = (
        "analyze_bank_statements",
        "User wants a summary or analysis of uploaded/imported bank statement records.",
        True,
        [
            "Analyze my bank statement.",
            "Summarize deposits and withdrawals.",
            "Show cash flow from my bank statement.",
        ],
    )

    TRAIN_CARD_MODEL = (
        "train_card_model",
        "User wants to train or retrain the credit card transaction labeling model.",
        True,
        [
            "Train the card model.",
            "Retrain transaction labels.",
        ],
    )

    TRAIN_STATEMENT_MODEL = (
        "train_statement_model",
        "User wants to train or retrain the bank statement labeling model.",
        True,
        [
            "Train the statement model.",
            "Retrain bank statement labels.",
        ],
    )

    REPREDICT_CARD_RECORDS = (
        "repredict_card_records",
        "User wants to regenerate predicted labels for existing credit card transaction records.",
        True,
        [
            "Repredict card records.",
            "Classify my card transactions again.",
        ],
    )

    REPREDICT_STATEMENT_RECORDS = (
        "repredict_statement_records",
        "User wants to regenerate predicted labels for existing bank statement records.",
        True,
        [
            "Repredict statement records.",
            "Classify my bank records again.",
        ],
    )

    LABEL_RECORDS = (
        "label_records",
        "User wants to manually assign, update, correct, or save labels/categories for records.",
        True,
        [
            "Label this record as Dining.",
            "Correct this category.",
            "Save this label.",
        ],
    )

    GENERAL_CHAT = (
        "general_chat",
        "User is asking a general question, coding question, explanation, or anything unrelated to an app workflow.",
        False,
        [
            "How do I write this Python function?",
            "Explain SQLAlchemy sessions.",
            "What is a database index?",
        ],
    )

    UNKNOWN = (
        "unknown",
        "The request is unclear, unsupported, or does not provide enough information to choose a safe intent.",
        False,
        [
            "Do it.",
            "Run that thing.",
            "Help me.",
        ],
    )

    def __new__(
        cls,
        value: str,
        description: str,
        needs_db: bool,
        examples: list[str],
    ):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.description = description
        obj.needs_db = needs_db
        obj.examples = examples
        return obj