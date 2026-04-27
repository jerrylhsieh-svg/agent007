from agent.models.labeling_job import InMemoryLabelingStore


GSHEET_NAME = "transactions"
GSHEET_TRANSACTIONS_TAB = "card_transactions"
GSHEET_STATEMENT_TAB = "bank_statements"
GSHEET_LABEL_TAB = "unknown_labels"
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

LABEL_HEADERS = [
    "sheet_name",
    "id",
    "description",
    "label",
]

labeling_store = InMemoryLabelingStore()