from __future__ import annotations


import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from agent.learning_models.constants import BASE_DIR
from agent.learning_models.transaction.merchant_rules import normalize_description



def train(csv_path: str, file_type: str) -> None:
    ARTIFACT_PATH = BASE_DIR / file_type / "artifacts" / "merchant_classifier.joblib"
    df = pd.read_csv(csv_path)

    required_columns = {"description", "label"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required CSV columns: {sorted(missing)}")

    df = df.dropna(subset=["description", "label"]).copy()
    label_counts = df["label"].value_counts()
    rare_labels = label_counts[label_counts < 2].index

    df["label"] = df["label"].replace(list(rare_labels), "other")
    df["text"] = df["description"].map(normalize_description)

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
    parser.add_argument("--csv", required=True, help="Path to labeled CSV")
    parser.add_argument("--file-type", required=True, help="file type")
    args = parser.parse_args()

    train(args.csv, args.file_type)