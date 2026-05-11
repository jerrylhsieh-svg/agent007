from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict
from functools import cached_property
from typing import Any

from fastapi import Depends
import pandas as pd

from agent.db.session import get_db_session
from agent.repo.financial_record_repository import FinancialRecordRepository
from agent.services.chat.call_model import call_model


class BaseFinancialAnalyzer(ABC):
    file_type: str

    def __init__(self):
        self.repo = FinancialRecordRepository(Depends(get_db_session), self.file_type)
        

    @cached_property
    def raw_df(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(record) for record in self.repo.get_records()])


    @cached_property
    def df(self) -> pd.DataFrame:
        return self.normalize_df(self.raw_df)

    @cached_property
    def total_days(self) -> int:
        if self.df.empty or "date" not in self.df.columns:
            return 1

        min_date = self.df["date"].min()
        max_date = self.df["date"].max()

        if pd.isna(min_date) or pd.isna(max_date):
            return 1

        return max((max_date - min_date).days, 1)

    def normalize_df(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df.copy()

        working = df.copy()

        working = self._coerce_common_types(working)

        return working
    

    def _coerce_common_types(self, df: pd.DataFrame) -> pd.DataFrame:
        if "amount" in df.columns:
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        
        df = df.dropna(subset=["amount"])

        return df


    def get_date_range(self, df: pd.DataFrame | None = None) -> dict[str, str | None]:
        working = self.df if df is None else df

        if working.empty or "date" not in working.columns:
            return {"start": None, "end": None}

        min_date = working["date"].min()
        max_date = working["date"].max()

        return {
            "start": None if pd.isna(min_date) else str(min_date.date()),
            "end": None if pd.isna(max_date) else str(max_date.date()),
        }

    def llm_answer(
        self,
        *,
        question: str,
        history: list[dict] | None,
        context: str,
    ) -> str:
        augmented_history = list(history or [])
        augmented_history.append({"role": "assistant", "content": context})
        return call_model(question, augmented_history)

    @abstractmethod
    def summarize(self) -> dict[str, Any]:
        raise NotImplementedError
