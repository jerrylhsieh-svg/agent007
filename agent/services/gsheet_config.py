GSHEET_NAME = "transactions"
GSHEET_TRANSACTIONS_TAB = "card_transactions"
GSHEET_STATEMENT_TAB = "bank_statement"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

TRANSACTION_HEADERS = [
    "upload_id",
    "source_file",
    "transaction_date",
    "posting_date",
    "description",
    "reference_number",
    "amount",
    "raw_line",
]

STATEMENT_HEADERS = [
    "upload_id",
    "source_file",
    "date",
    "description",
    "statement_type",
    "amount",
    "raw_line",
]