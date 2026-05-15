import io
from typing import Literal
import pandas as pd
from sqlalchemy.orm import Session

from agent.db.data_classes.label import TrainRecord
from agent.repo.train_record_repository import TrainRecordRepository


class LabeledCsvUploadService:
    REQUIRED_COLUMNS = {"description", "label"}

    def __init__(self, db: Session):
        self.db = db
        self.file_type: Literal['transaction', 'statement'] = "transaction"

    def upload(self, content: bytes) -> dict[str, int]:
        try:
            df = pd.read_csv(io.BytesIO(content))
        except Exception as exc:
            raise ValueError(f"Invalid CSV file: {exc}") from exc

        missing = self.REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
        if "statement_type" in set(df.columns):
            self.file_type = "statement"

        df = df.dropna(subset=["description", "label"])

        repo = TrainRecordRepository(self.db, record_type=self.file_type)

        trained_records = []
        for _, row in df.iterrows():
            description = str(row["description"]).strip()
            label = str(row["label"]).strip()

            statement_type = ""
            if "statement_type" in df.columns and pd.notna(row["statement_type"]):
                statement_type = str(row["statement_type"]).strip().lower()
            
            if len(statement_type) > 0 and statement_type not in ("deposit", "withdraw"):
                raise ValueError("statement_type has to be either deposit or withdraw")

            trained_records.append(TrainRecord(
                description=description,
                label=label,
                statement_type=statement_type,
            ))

        repo.insert_many(trained_records)
        inserted = len(trained_records)

        return {
            "inserted": inserted,
        }