from agent.models.label import InMemoryLabelingStore


GSHEET_NAME = "transactions"
GSHEET_TRANSACTIONS_TAB = "card_transactions"
GSHEET_STATEMENT_TAB = "bank_statements"
GSHEET_LABEL_TRANSACTIONS_TAB = "unknown_transactions_labels"
GSHEET_LABEL_STATEMENTS_TAB = "unknown_statements_labels"
GSHEET_LABEL_TRANSACTION_GROUP_TAB = "unknown_transaction_labels_group"
GSHEET_LABEL_STATEMENT_GROUP_TAB = "unknown_statement_labels_group"
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

STATEMENT_LABEL_HEADERS = [
    "record_id", 
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