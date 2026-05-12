from typing import Literal

from sqlalchemy.orm import Session

from agent.learning_models.labeler import Labeler
from agent.repo.financial_record_repository import FinancialRecordRepository
from agent.services.chat.call_model import call_model


def repredict_records(
    question: str,
    file_type: Literal["transaction", "statement"],
    db: Session,
    history: list[dict] | None = None,
) -> str:
    
    predictor = Labeler(file_type=file_type)
    repo = FinancialRecordRepository(db, file_type)

    records = repo.get_records()

    if records is None:
        raise ValueError("No record found")

    updated_count = 0
    changed_count = 0

    for record in records:
        old_label = record.label
        record.label = predictor.predict_one(record.description).predicted_label

        repo.update_record(record)

        updated_count += 1
        if old_label != record.label:
            changed_count += 1

    context = f"""
        Re-prediction completed for {file_type}. 
        Updated {updated_count} unconfirmed records. 
        {changed_count} predictions changed. 
        Human-confirmed labels were not overwritten.
    """

    history = history or []
    history.append({"role": "assistant", "content": context})
    return call_model(question, history)
