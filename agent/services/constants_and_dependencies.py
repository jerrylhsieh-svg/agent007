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
    "record_id", 
    "sheet_name", 
    "description",
    "normalized_description",
    "predicted_label",
    "confidence",
    "priority_score",
    "similar_count",
    "total_amount_impact",
]

labeling_store = InMemoryLabelingStore()