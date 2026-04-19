from __future__ import annotations

from collections import Counter
from functools import cached_property
from fastapi import HTTPException

import pandas as pd

from agent.services.call_model import call_model
from agent.services.google_sheets import read_transactions_df
from agent.services.gsheet_config import GSHEET_NAME, GSHEET_TRANSACTIONS_TAB
from agent.services.helper import thirty_days_avg

class CreditCardTransactionAnalyzer:        
    @cached_property
    def df(self) -> pd.DataFrame:
        return read_transactions_df(
            spreadsheet_name=GSHEET_NAME,
            worksheet_name=GSHEET_TRANSACTIONS_TAB,
        )
    

    def _normalize_transaction_df(self) -> pd.DataFrame:
        if self.df.empty:
            raise HTTPException(status_code=400, detail="Empty Transaction DataFrame")

        working = self.df.copy()

        working["amount"] = pd.to_numeric(working["amount"], errors="coerce")
        working = working.dropna(subset=["amount"])

        return working
        
    
    def summarize_transactions(self) -> dict:
        working = self._normalize_transaction_df()
        expenses = working[working["amount"] >= 0].copy()

        total_spend = round(abs(expenses["amount"].sum()), 2) if not expenses.empty else 0.0

        min_date = working["date"].min() 
        max_date = working["date"].max() 
        total_date = (max_date-min_date).days

        merchant_counter: Counter[str] = Counter()
        if "description" in expenses.columns:
            for desc in expenses["description"].fillna(""):
                normalized = " ".join(str(desc).strip().split())
                if normalized:
                    merchant_counter[normalized[:80]] += 1

        return {
            "row_count": int(len(working)),
            "date_range": {
                "start": None if pd.isna(min_date) else str(min_date.date()),
                "end": None if pd.isna(max_date) else str(max_date.date()),
            },
            "total_spend": total_spend,
            "30 days spend avg": thirty_days_avg(total_spend, total_date),
        }


def generate_credit_card_summary(question: str, history: list[dict] | None = None) -> str:
    history = history or []
    credit_analyzer = CreditCardTransactionAnalyzer()
    summary = credit_analyzer.summarize_transactions()

    if summary["row_count"] == 0:
        return "I couldn't find any transaction rows in Google Sheets yet."

    context = f"""
You are analyzing personal transaction data stored in Google Sheets.

Dataset summary:
- Row count: {summary["row_count"]}
- Date range: {summary["date_range"]}
- Total spend: {summary["total_spend"]}
- 30 days withdraw avgerage: {summary["30 days spend avg"]}

Answer the user's question using only this transaction context.
If the data is insufficient, say what is missing.
Be concrete and numeric where possible.
"""

    augmented_history = list(history)
    augmented_history.append({"role": "assistant", "content": context})

    return call_model(question, augmented_history)