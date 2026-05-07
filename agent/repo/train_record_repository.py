from dataclasses import asdict
from typing import Literal

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from agent.db.data_classes.label import TrainRecord
from agent.db.models.trained.BankStatementTrained import BankStatementTrained
from agent.db.models.trained.TransactionTrained import TransactionTrained

RecordType = Literal["transaction", "statement"]

class TrainRecordRepository:
    


    def __init__(self, db: Session, record_type: RecordType):
        self.db = db
        self.record_type = record_type
        if record_type == "statement":
            self.record_class = BankStatementTrained  
        else: 
            self.record_class = TransactionTrained

    def _to_db_record(self, record: TrainRecord):
        columns = set(self.record_class.__table__.columns.keys())

        data = {
            key: value
            for key, value in asdict(record).items()
            if key in columns and value is not None
        }

        return self.record_class(**data)

    def insert_many(self, records: list[TrainRecord]) -> None:
        db_records = []
        for record in records:
            db_records.append(self._to_db_record(record))

        self.db.add_all(db_records)
        self.db.commit()
    
    def get_records(self) -> list[TrainRecord]:
        stmt = select(self.record_class)
        rows = self.db.scalars(stmt).all()

        return [
            TrainRecord(
                id=row.id,
                description=row.description,
                label=row.label,
                statement_type=getattr(row, "statement_type", ""),
            )
            for row in rows
        ]

    def get_record(self, id: int) -> TrainRecord:
        row = self.db.get(self.record_class, id)

        if row is None:
            raise ValueError(f"{self.record_type} record with id={id} not found")

        return TrainRecord(id=id, description=row.description, label=row.description, statement_type=getattr(row, "statement_type", ""),)

    def update_record(self, record: TrainRecord) -> None:
        if record.id is None:
            raise ValueError("id is required when updating a trained record")
        
        row = self.db.get(self.record_class, record.id)

        if row is None:
            raise ValueError(f"{self.record_type} record with id={record.id} not found")

        row.id = record.id
        row.description = record.description
        row.label = record.label

        if "statement_type" in self.record_class.__table__.columns:
            row.statement_type = record.statement_type or ""

        self.db.commit()

    def delete_record(self, record_id: str) -> None:
        row = self.db.get(self.record_class, record_id)

        if row is None:
            raise ValueError(f"{self.record_type} record with id={record_id} not found")

        self.db.delete(row)
        self.db.commit()
    
    def overwrite_all(self, records: list[TrainRecord]) -> None:
        self.db.query(self.record_class).delete()
        db_records = [self._to_db_record(record) for record in records]

        self.db.add_all(db_records)
        self.db.commit()

    def to_df(self) -> pd.DataFrame:
        records = self.get_records()

        return pd.DataFrame([asdict(record) for record in records])