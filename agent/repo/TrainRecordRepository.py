from dataclasses import asdict

import pandas as pd

from agent.models.label import TrainRecord
from agent.services.constants_and_dependencies import GSHEET_NAME, TRAIN_RECORD_HEADERS
from agent.services.google_sheets import append_data, build_gsheet_rows, get_or_create_worksheet


class TrainRecordRepository:
    def __init__(self, worksheet_name):
        self.worksheet_name = worksheet_name
        self.worksheet = get_or_create_worksheet(spreadsheet_name=GSHEET_NAME, worksheet_name=worksheet_name)
    

    def insert_many(self, records: list[TrainRecord]) -> None:
        fields = TRAIN_RECORD_HEADERS
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

    def get_records(self) -> list[TrainRecord]:
        rows = self.worksheet.get_all_records()

        return [
            TrainRecord(**row)
            for row in rows
        ]

    def to_df(self) -> pd.DataFrame:
        records = self.get_records()
        return pd.DataFrame([asdict(record) for record in records])
