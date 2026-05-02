# agent/services/repredict_service.py

from typing import Literal

from agent.learning_models.labeler import Labeler
from agent.repo.FinacialRecordRepository import FinacialRecordRepository


def repredict_records(
    question: str,
    file_type: Literal["transaction", "statement"],
    history: list[dict] | None = None,
) -> str:
    repo = FinacialRecordRepository(file_type=file_type)
    predictor = Labeler(file_type=file_type)

    records = repo.get_records()

    updated_count = 0
    changed_count = 0

    for record in records:
        old_label = record.label
        record.label = predictor.predict_one(record.description)

        repo.update_record(record)

        updated_count += 1
        if old_label != record.label.predicted_label:
            changed_count += 1

    return (
        f"Re-prediction completed for {file_type}. "
        f"Updated {updated_count} unconfirmed records. "
        f"{changed_count} predictions changed. "
        "Human-confirmed labels were not overwritten."
    )