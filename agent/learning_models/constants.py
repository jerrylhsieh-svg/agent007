import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = Path(os.getenv("MODEL_ARTIFACT_DIR", "/models"))
TRANSACTION_ARTIFACT_PATH = MODEL_DIR / "transaction" / "artifacts" / "merchant_classifier.joblib"
STATEMENT_ARTIFACT_PATH = MODEL_DIR / "statement" / "artifacts" / "merchant_classifier.joblib"
UNKNOWN_LABEL = "unknown"
BASE_LABELED_CSV = "data/{file_type}/description_labeled.csv"
TRAINING_CONFIG = {
    "transaction": {
        "required_columns": {"description", "label"},
    },
    "statement": {
        "required_columns": {"description", "statement_type", "label"},
    },
}