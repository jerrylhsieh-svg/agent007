from __future__ import annotations
import re


import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from agent.learning_models.constants import BASE_DIR, BASE_LABELED_CSV, TRAINING_CONFIG


def normalize_description(text: str) -> str:
    normalized = text.lower()
    normalized = normalized.replace("*", " ")
    normalized = re.sub(r"\d{3,}", " ", normalized)
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized

def build_training_text(df: pd.DataFrame, file_type: str) -> pd.Series:
    if file_type == "transaction":
        return df["description"].map(normalize_description)

    if file_type == "statement":
        return (
            df["statement_type"].astype(str).str.lower().str.strip()
            + " "
            + df["description"].map(normalize_description)
        )

    raise ValueError(f"Unsupported file_type: {file_type}")

def train(file_type: str) -> None:
    ARTIFACT_PATH = BASE_DIR / file_type / "artifacts" / "merchant_classifier.joblib"
    config = TRAINING_CONFIG[file_type]
    csv_path = BASE_LABELED_CSV.format(file_type=file_type)
    df = pd.read_csv(csv_path)

    required_columns = config["required_columns"]
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required CSV columns: {sorted(missing)}")

    df = df.dropna(subset=list(required_columns)).copy()

    if file_type == "statement":
        valid_statement_types = {"deposit", "withdraw"}
        invalid_types = set(df["statement_type"]) - valid_statement_types

        if invalid_types:
            raise ValueError(
                f"Invalid statement_type values: {sorted(invalid_types)}. "
                f"Expected: {sorted(valid_statement_types)}"
            )

    label_counts = df["label"].value_counts()
    rare_labels = label_counts[label_counts < 2].index

    df["label"] = df["label"].replace(list(rare_labels), "other")
    df["text"] = build_training_text(df, file_type)

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"],
        df["label"],
        test_size=0.2,
        random_state=42,
        stratify=df["label"],
    )

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.95,
                    max_features=50_000,
                    sublinear_tf=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                ),
            ),
        ]
    )

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    print(classification_report(y_test, predictions))

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, ARTIFACT_PATH)

    print(f"Saved model artifact to: {ARTIFACT_PATH}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file-type", required=True, help="file type")
    args = parser.parse_args()

    train(args.file_type)