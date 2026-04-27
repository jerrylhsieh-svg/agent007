from dataclasses import asdict

from agent.models.labeling_job import UnlabeledRecord
from agent.services.constants_and_dependencies import GSHEET_LABEL_TAB, GSHEET_NAME, LABEL_HEADERS
from agent.services.google_sheets import append_data, build_gsheet_rows, get_or_create_worksheet


class UnlabeledRecordRepository:
    def __init__(self):
        self.worksheet = get_or_create_worksheet(spreadsheet_name=GSHEET_NAME, worksheet_name=GSHEET_LABEL_TAB)

    def insert_many(self, records: list[UnlabeledRecord], worksheet_name=GSHEET_LABEL_TAB) -> None:
        rows = build_gsheet_rows(
            data=[asdict(row) for row in records],
            fields=LABEL_HEADERS,
        )
        
        append_data(
            spreadsheet_name=GSHEET_NAME,
            worksheet_name=worksheet_name,
            rows=rows,
            headers=LABEL_HEADERS
        )

    def get_records(self) -> list[UnlabeledRecord]:
        rows = self.worksheet.get_all_records()

        return [
            UnlabeledRecord(**row)
            for row in rows
        ]

    def overwrite(self, records: list[UnlabeledRecord], worksheet_name=GSHEET_LABEL_TAB) -> None:
        worksheet = get_or_create_worksheet(spreadsheet_name=GSHEET_NAME, worksheet_name=worksheet_name)
        worksheet.clear()
        self.insert_many(records, worksheet_name=worksheet_name)
