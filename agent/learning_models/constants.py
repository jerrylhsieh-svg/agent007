from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TRANSACTION_ARTIFACT_PATH = BASE_DIR / "transaction" / "artifacts" / "merchant_classifier.joblib"
STATEMENT_ARTIFACT_PATH = BASE_DIR / "statement" / "artifacts" / "merchant_classifier.joblib"
UNKNOWN_LABEL = "unknown"