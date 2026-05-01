from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TRANSACTION_ARTIFACT_PATH = BASE_DIR / "transaction" / "artifacts" / "merchant_classifier.joblib"
STATEMENT_ARTIFACT_PATH = BASE_DIR / "statement" / "artifacts" / "merchant_classifier.joblib"
UNKNOWN_LABEL = "unknown"
BASE_LABELED_CSV = "data/{file_type}/description_labeled.csv"
TRAINING_CONFIG = {
    "transaction": {
        "required_columns": {"description", "label"},
        "worksheet": "transaction_train_data",
    },
    "statement": {
        "required_columns": {"description", "statement_type", "label"},
        "worksheet": "statement_train_data",
    },
}