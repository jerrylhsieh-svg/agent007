from agent.models.labeling_job import InMemoryLabelingStore


GSHEET_NAME = "transactions"
GSHEET_TRANSACTIONS_TAB = "card_transactions"
GSHEET_STATEMENT_TAB = "bank_statements"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

TRANSACTION_HEADERS = [
    "upload_id",
    "source_file",
    "date",
    "description",
    "amount",
    "label",
]

STATEMENT_HEADERS = [
    "upload_id",
    "source_file",
    "date",
    "description",
    "statement_type",
    "amount",
    "label",
]

labeling_store = InMemoryLabelingStore()