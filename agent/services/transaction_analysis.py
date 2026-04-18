from __future__ import annotations

from collections import Counter
from http.client import HTTPException

import pandas as pd

from agent.services.call_model import call_model
from agent.services.google_sheets import read_transactions_df
from agent.services.gsheet_config import GSHEET_NAME, GSHEET_TRANSACTIONS_TAB
from agent.services.helper import _safe_float

class CreditCardTransactionAnalyzer:

    def __init__(self):
        self.df = self._retrieve_transaction()
        self._debits = None
        self._credits = None
        self._monthly_summary = None

    
    def _retrieve_transaction(self) -> pd.DataFrame:

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

        top_merchants = [
            {"merchant": name, "count": count}
            for name, count in merchant_counter.most_common(10)
        ]

        monthly_spend = []
        if "date" in expenses.columns and not expenses.empty:
            monthly = (
                expenses.dropna(subset=["date"])
                .assign(month=lambda x: x["date"].dt.to_period("M").astype(str))
                .groupby("month", as_index=False)["amount"]
                .sum()
            )
            monthly["amount"] = monthly["amount"].abs().round(2)
            monthly_spend = monthly.sort_values("month").to_dict(orient="records")

        latest_transactions = []
        sort_cols = [c for c in ["date", "page_number"] if c in working.columns]
        latest = (
            working.sort_values(sort_cols, ascending=False)
            if sort_cols
            else working
        ).head(15)

        for _, row in latest.iterrows():
            latest_transactions.append(
                {
                    "date": None if pd.isna(row.get("date")) else str(row["date"].date()),
                    "description": row.get("description"),
                    "amount": _safe_float(row.get("amount")),
                    "balance": _safe_float(row.get("balance")),
                    "source_file": row.get("source_file"),
                }
            )

        return {
            "row_count": int(len(working)),
            "date_range": date_range,
            "total_spend": total_spend,
            "total_income": total_income,
            "net_amount": net_amount,
            "top_merchants": top_merchants,
            "monthly_spend": monthly_spend,
            "latest_transactions": latest_transactions,
        }


def analyze_transactions_question(question: str, history: list[dict] | None = None) -> str:
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

Top merchants:
{summary["top_merchants"]}

Monthly spend:
{summary["monthly_spend"]}

Latest transactions:
{summary["latest_transactions"]}

Answer the user's question using only this transaction context.
If the data is insufficient, say what is missing.
Be concrete and numeric where possible.
"""

    augmented_history = list(history)
    augmented_history.append({"role": "assistant", "content": context})

    return call_model(question, augmented_history)