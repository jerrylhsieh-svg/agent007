from dataclasses import asdict

from agent.models.label import UnlabeledRecord
from agent.services.constants_and_dependencies import GSHEET_NAME
from agent.services.google_sheets import append_data, build_gsheet_rows, get_or_create_worksheet


class UnlabeledRecordRepository:
    def __init__(self, worksheet_name):
        self.worksheet_name = worksheet_name
        self.worksheet = get_or_create_worksheet(spreadsheet_name=GSHEET_NAME, worksheet_name=worksheet_name)

    def insert_many(self, records: list[UnlabeledRecord], fields: list[str]) -> None:
        rows = build_gsheet_rows(
            data=[asdict(row) for row in records],
            fields=fields,
        )
        
        append_data(
            spreadsheet_name=GSHEET_NAME,
            worksheet_name=self.worksheet_name,
            rows=rows,
            headers=fields
        )

    def get_records(self) -> list[UnlabeledRecord]:
        rows = self.worksheet.get_all_records()

        return [
            UnlabeledRecord(**row)
            for row in rows
        ]
    
    def get_first_record(self) -> UnlabeledRecord | None:
        records = self.get_records()
        return records[0] if records else None

    def overwrite(self, records: list[UnlabeledRecord], fields: list[str]) -> None:
        self.worksheet.clear()
        self.insert_many(records, fields)

    def delete_record(self, record: UnlabeledRecord) -> None:
        rows = self.worksheet.get_all_records()

        for index, row in enumerate(rows, start=1):
            if row.get("id") == record.id:
                self.worksheet.delete_rows(index)
                return

        raise ValueError(f"Record with id={record.id} not found")
