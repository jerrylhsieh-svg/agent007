
from dataclasses import asdict
from typing import Any

from agent.models.pdf_models import BankStatementRow, TransactionRow
from agent.services.constants_and_dependencies import GSHEET_NAME
from agent.services.google_sheets import get_or_create_worksheet


class FinacialRecordRepository:
    def __init__(self, worksheet_name):
        self.worksheet_name = worksheet_name
        self.record_type = "transaction" if self.worksheet_name == "card_transactions" else "statement"
        self.worksheet = get_or_create_worksheet(spreadsheet_name=GSHEET_NAME, worksheet_name=worksheet_name)

    def get_records(self) -> list[TransactionRow] | list[BankStatementRow]:
        rows = self.worksheet.get_all_records()

        return [
            TransactionRow(**row)
            for row in rows
        ] if self.worksheet_name == "card_transactions" else [
            BankStatementRow(**row)
            for row in rows
        ]
    
    def update_record(self, record: TransactionRow | BankStatementRow) -> None:
        rows = self.worksheet.get_all_records()

        if not rows:
            raise ValueError("Worksheet is empty")

        row_index = None

        for index, row in enumerate(rows, start=2): 
            if row.get("id") == record.id:
                row_index = index
                break

        if row_index is None:
            raise ValueError(f"Record with id={record.id} not found")

        headers = self.worksheet.row_values(1)
        header_to_col = {
            header: index
            for index, header in enumerate(headers, start=1)
        }

        for field_name, value in asdict(record).items():
            col_index = header_to_col[field_name]
            self.worksheet.update_cell(row_index, col_index, value)