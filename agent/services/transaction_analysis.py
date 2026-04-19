from __future__ import annotations

from collections import Counter
from functools import cached_property
from http.client import HTTPException

import pandas as pd

from agent.services.call_model import call_model
from agent.services.google_sheets import read_transactions_df
from agent.services.gsheet_config import GSHEET_NAME, GSHEET_TRANSACTIONS_TAB

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
        expenses = working[working["amount"] < 0].copy()
        income = working[working["amount"] > 0].copy()

        total_spend = round(abs(expenses["amount"].sum()), 2) if not expenses.empty else 0.0
        total_income = round(income["amount"].sum(), 2) if not income.empty else 0.0
        net_amount = round(working["amount"].sum(), 2)

        if "date" in working.columns:
            min_date = working["date"].min()
            max_date = working["date"].max()
            date_range = {
                "start": None if pd.isna(min_date) else str(min_date.date()),
                "end": None if pd.isna(max_date) else str(max_date.date()),
            }
        else:
            date_range = None

        merchant_counter = Counter()
        if "description" in expenses.columns:
            for desc in expenses["description"].fillna(""):
                normalized = " ".join(str(desc).strip().split())
                if normalized:
                    merchant_counter[normalized[:80]] += 1

        return {
            "row_count": int(len(working)),
            "date_range": date_range,
            "total_spend": total_spend,
            "total_income": total_income,
            "net_amount": net_amount,
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
- Total income: {summary["total_income"]}
- Net amount: {summary["net_amount"]}

Answer the user's question using only this transaction context.
If the data is insufficient, say what is missing.
Be concrete and numeric where possible.
"""

    augmented_history = list(history)
    augmented_history.append({"role": "assistant", "content": context})

    return call_model(question, augmented_history)