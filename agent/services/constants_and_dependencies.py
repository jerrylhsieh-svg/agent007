import re

from agent.db.data_classes.label import InMemoryLabelingStore


GSHEET_NAME = "transactions"
GSHEET_TRANSACTIONS_TAB = "card_transactions"
GSHEET_STATEMENT_TAB = "bank_statements"
GSHEET_LABEL_TRANSACTIONS_TAB = "unknown_transactions_labels"
GSHEET_LABEL_STATEMENTS_TAB = "unknown_statements_labels"
GSHEET_LABEL_TRANSACTION_GROUP_TAB = "unknown_transaction_labels_group"
GSHEET_LABEL_STATEMENT_GROUP_TAB = "unknown_statement_labels_group"
GSHEET_LABEL_TRANSACTION_TRAIN_TAB = "transaction_train_data"
GSHEET_LABEL_STATEMENT_TRAIN_TAB = "statement_train_data"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

TRANSACTION_HEADERS = [
    "id",
    "date",
    "description",
    "amount",
    "label",
]

STATEMENT_HEADERS = [
    "id",
    "date",
    "description",
    "statement_type",
    "amount",
    "label",
]

TRANSACTION_LABEL_HEADERS = [
    "id", 
    "sheet_name", 
    "description",
    "normalized_description",
    "predicted_label",
    "confidence",
    "priority_score",
    "similar_count",
    "total_amount_impact",
]

STATEMENT_LABEL_HEADERS = [
    "id", 
    "sheet_name", 
    "description",
    "statement_type",
    "normalized_description",
    "predicted_label",
    "confidence",
    "priority_score",
    "similar_count",
    "total_amount_impact",
]

TRAIN_RECORD_HEADERS = [
    "description",
    "statement_type",
    "label",
]

ALLOWED_TRANSACTION_LABELS = [
    "Merchandise",
    "Entertainment",
    "Travel and Transportation",
    "Health",
    "Services",
    "Dining",
    "Housing"
]

ALLOWED_STATEMENT_LABELS = [
    "Card payment",
    "Investment",
    "Income"
]

labeling_store = InMemoryLabelingStore()

SAVE_TRIGGERS = {
    "help me write a file",
    "write a file",
    "create a file",
    "save a file",
    "make a file",
}

IS_TRANSACTION_TRIGGERS = [
    "credit card spending summary",
]

IS_STATEMENT_TRIGGERS = [
    "bank statement summary",
]

IS_WITHDRAW_TRIGGERS = [
    "bank withdraw summary",
]

IS_STATEMENT_TRAIN_TRIGGERS = [
    "train statement model",
]

IS_TRANSACTION_TRAIN_TRIGGERS = [
    "train transaction model",
]

IS_STATEMENT_PREDICT_TRIGGERS = [
    "yes re-predict statement",
]

IS_TRANSACTION_PREDICT_TRIGGERS = [
    "yes re-predict transaction",
]

IS_LABEL_TRIGGERS = [
    "help with labeling",
    "transaction",
    "statement",
    "approve",
    "not approve"
]

MONTH_RE = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?"

STATEMENT_PERIOD_RE = re.compile(
    rf"""
    (?P<start_month>{MONTH_RE}|\d{{1,2}})
    [\s/-]+
    (?P<start_day>\d{{1,2}})
    (?:,?\s*
        (?P<start_year>\d{{4}})
    )?

    \s*
    (?:
        to
        |
        through
        |
        thru
        |
        -
        |
        –
        |
        —
    )
    \s*

    (?P<end_month>{MONTH_RE}|\d{{1,2}})
    [\s/-]+
    (?P<end_day>\d{{1,2}})
    (?:,?\s*
        (?P<end_year>\d{{4}})
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


DATE_RE = re.compile(
    r"""
    ^
    (?:
        # 2024-01-31, 2024/1/31, 2024.01.31
        \d{4}[-/.]\d{1,2}[-/.]\d{1,2}

        |

        # 01/31, 1/31/24, 01-31-2024, 1.31.2024
        \d{1,2}/\d{1,2}(?:/\d{2,4})?

        |

        # Jan 31, January 31, Jan 31 2024, January 31, 2024
        (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)
        [a-z]*\.?\s+\d{1,2}(?:,?\s+\d{2,4})?

        |

        # 31 Jan, 31 January 2024
        \d{1,2}\s+
        (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)
        [a-z]*\.?(?:,?\s+\d{2,4})?
    )
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)

MONTH_LOOKUP = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}
