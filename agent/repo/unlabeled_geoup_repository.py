from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from agent.db.data_classes.label import UnlabeledRecord
from agent.db.models.unlabeled.UnlabeledStatementGroup import UnlabeledStatementGroup
from agent.db.models.unlabeled.UnlabeledTransactionGroup import UnlabeledTransactionGroup

RecordType = Literal["transaction", "statement"]

class UnlabeledGroupRepository:
    def __init__(self, db: Session, record_type: RecordType):
        self.db = db
        self.record_type = record_type
        if record_type == "statement":
            self.record_class = UnlabeledStatementGroup  
        else: 
            self.record_class = UnlabeledTransactionGroup

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
                similar_count=record.similar_count,
                record_type=self.record_type,
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
                total_amount_impact=row.total_amount_impact,
                predicted_label=row.predicted_label,
                confidence=row.confidence,
                priority_score=row.priority_score,
                similar_count=row.similar_count,
                record_type=self.record_type,
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
            total_amount_impact=row.total_amount_impact,
            predicted_label=row.predicted_label,
            confidence=row.confidence,
            priority_score=row.priority_score,
            similar_count=row.similar_count,
            record_type=self.record_type,
        )
    
    def yield_record_by_score(self) -> UnlabeledRecord | None:
        stmt = select(self.record_class).order_by(self.record_class.priority_score.desc()).limit(1)
        row = self.db.scalars(stmt).first()

        if row is None: return row

        return UnlabeledRecord(
            id=row.id,
            description=row.description,
            normalized_description=row.normalized_description,
            total_amount_impact=row.total_amount_impact,
            predicted_label=row.predicted_label,
            confidence=row.confidence,
            priority_score=row.priority_score,
            similar_count=row.similar_count,
            record_type=self.record_type,
        )

    def update_record(self, record: UnlabeledRecord) -> None:
        row = self.db.get(self.record_class, record.id)

        if row is None:
            raise ValueError(f"{self.record_type} record with id={record.id} not found")

        row.id=record.id
        row.description=record.description
        row.normalized_description=record.normalized_description
        row.total_amount_impact=record.total_amount_impact
        row.predicted_label=record.predicted_label
        row.confidence=record.confidence
        row.priority_score=record.priority_score
        row.similar_count=record.similar_count

        self.db.commit()

    def delete_record(self, record_id: str) -> None:
        row = self.db.get(self.record_class, record_id)

        if row is None:
            raise ValueError(f"{self.record_type} record with id={record_id} not found")

        self.db.delete(row)
        self.db.commit()
    
    def upsert_many(self, records: list[UnlabeledRecord]) -> None:
        for record in records:
            db_record = self.record_class(
                id=record.id,
                description=record.description,
                normalized_description=record.normalized_description,
                total_amount_impact=record.total_amount_impact,
                predicted_label=record.predicted_label,
                confidence=record.confidence,
                priority_score=record.priority_score,
                similar_count=record.similar_count,
            )

            self.db.merge(db_record)

        self.db.commit()