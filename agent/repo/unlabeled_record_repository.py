from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from agent.db.data_classes.label import UnlabeledRecord
from agent.db.models.unlabeled.UnlabeledStatementRecord import UnlabeledStatementnRecord
from agent.db.models.unlabeled.UnlabeledTransactionRecord import UnlabeledTransactionRecord

RecordType = Literal["transaction", "statement"]

class UnlabeledRecordRepository:
    def __init__(self, db: Session, record_type: RecordType):
        self.db = db
        self.record_type = record_type
        if record_type == "statement":
            self.record_class = UnlabeledStatementnRecord  
        else: 
            self.record_class = UnlabeledTransactionRecord

    def insert_many(self, records: list[UnlabeledRecord]) -> None:
        db_records = [
            self.record_class(
                id=record.id,
                description=record.description,
                normalized_description=record.normalized_description,
                amount=record.total_amount_impact,
                predicted_label=record.predicted_label,
                confidence=record.confidence,
                priority_score=record.priority_score,
            )
            for record in records
        ]

        self.db.add_all(db_records)
        self.db.commit()

    def get_records(self) -> list[UnlabeledRecord]:
        stmt = select(self.record_class).order_by(self.record_class.priority_score)
        rows = self.db.scalars(stmt).all()

        return [
            UnlabeledRecord(
                id=row.id,
                description=row.description,
                normalized_description=row.normalized_description,
                total_amount_impact=row.amount,
                predicted_label=row.predicted_label,
                confidence=row.confidence,
                priority_score=row.priority_score,
                similar_count=1,
            )
            for row in rows
        ]

    def get_record_by_id(self, record_id: str) -> UnlabeledRecord:
        row = self.db.get(self.record_class, record_id)

        if row is None:
            raise ValueError(f"{self.record_type} record with id={record_id} not found")

        return UnlabeledRecord(
            id=row.id,
            description=row.description,
            normalized_description=row.normalized_description,
            total_amount_impact=row.amount,
            predicted_label=row.predicted_label,
            confidence=row.confidence,
            priority_score=row.priority_score,
            similar_count=1,
        )

    def update_record(self, record: UnlabeledRecord) -> None:
        row = self.db.get(self.record_class, record.id)

        if row is None:
            raise ValueError(f"{self.record_type} record with id={record.id} not found")

        row.id=record.id
        row.description=record.description
        row.normalized_description=record.normalized_description
        row.amount=record.total_amount_impact
        row.predicted_label=record.predicted_label
        row.confidence=record.confidence
        row.priority_score=record.priority_score

        self.db.commit()

    def delete_record(self, record_id: str) -> None:
        row = self.db.get(self.record_class, record_id)

        if row is None:
            raise ValueError(f"{self.record_type} record with id={record_id} not found")

        self.db.delete(row)
        self.db.commit()