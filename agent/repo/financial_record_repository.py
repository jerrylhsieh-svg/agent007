from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from agent.db.models.BankStatementRecord import BankStatementRecord
from agent.db.models.TransactionRecord import TransactionRecord
from agent.db.data_classes.pdf_models import FinancialRecordRow


RecordType = Literal["transaction", "statement"]


class FinancialRecordRepository:
    def __init__(self, db: Session, record_type: RecordType):
        self.db = db
        self.record_type = record_type
        if record_type == "statement":
            self.record_class = BankStatementRecord  
        else: 
            self.record_class = TransactionRecord


    def insert_many(self, records: list[FinancialRecordRow]) -> None:
        db_records = [
            self.record_class(
                id=record.id,
                date=record.date,
                description=record.description,
                amount=record.amount,
                label=record.label,
            )
            for record in records
        ]

        self.db.add_all(db_records)
        self.db.commit()

    def get_records(self) -> list[FinancialRecordRow] | None:
        stmt = select(self.record_class).order_by(self.record_class.date)
        rows = self.db.scalars(stmt).all()

        return [
            FinancialRecordRow(
                id=row.id,
                date=row.date,
                description=row.description,
                amount=row.amount,
                label=row.label,
            )
            for row in rows
        ]

    def get_record_by_id(self, record_id: str) -> FinancialRecordRow:
        row = self.db.get(self.record_class, record_id)

        if row is None:
            raise ValueError(f"{self.record_type} record with id={record_id} not found")

        return FinancialRecordRow(
            id=row.id,
            date=row.date,
            description=row.description,
            amount=row.amount,
            label=row.label,
        )

    def update_record(self, record: FinancialRecordRow) -> None:
        row = self.db.get(self.record_class, record.id)

        if row is None:
            raise ValueError(f"{self.record_type} record with id={record.id} not found")

        row.date = record.date
        row.description = record.description
        row.amount = record.amount
        row.label = record.label

        self.db.commit()

    def delete_record(self, record_id: str) -> None:
        row = self.db.get(self.record_class, record_id)

        if row is None:
            raise ValueError(f"{self.record_type} record with id={record_id} not found")

        self.db.delete(row)
        self.db.commit()

    def get_unlabeled_records(self) -> list[FinancialRecordRow]:
        stmt = (
            select(self.record_class)
            .where(self.record_class.label == "")
            .order_by(self.record_class.date)
        )

        rows = self.db.scalars(stmt).all()

        return [
            FinancialRecordRow(
                id=row.id,
                date=row.date,
                description=row.description,
                amount=row.amount,
                label=row.label,
            )
            for row in rows
        ]