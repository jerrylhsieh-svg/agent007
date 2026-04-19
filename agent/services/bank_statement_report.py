from __future__ import annotations

from functools import cached_property
from typing import Any

import pandas as pd

from agent.services.call_model import call_model
from agent.services.google_sheets import read_transactions_df
from agent.services.gsheet_config import GSHEET_NAME, GSHEET_STATEMENT_TAB
from agent.services.helper import thirty_days_avg

class BankStatementAnalyzer:
    @cached_property
    def df(self) -> pd.DataFrame:
        return read_transactions_df(
            spreadsheet_name=GSHEET_NAME,
            worksheet_name=GSHEET_STATEMENT_TAB,
        )
    

    def _normalize_statement_df(self) -> pd.DataFrame:
        if self.df.empty:
            return self.df.copy()

        working = self.df.copy()

        # tolerate a couple of possible date column names
        if "date" not in working.columns:
            for candidate in ("transaction_date", "posting_date"):
                if candidate in working.columns:
                    working["date"] = working[candidate]
                    break

        if "date" in working.columns:
            working["date"] = pd.to_datetime(working["date"], errors="coerce")

        if "amount" in working.columns:
            working["amount"] = pd.to_numeric(working["amount"], errors="coerce")

        for col in ("description", "statement_type", "source_file", "raw_line"):
            if col not in working.columns:
                working[col] = None
        
        working = working.dropna(subset=["amount"])

        return working


    def summarize_statement_data(self) -> dict[str, Any]:
        summary = self.df

        withdraw = summary[summary["statement_type"] == "withdraw"].copy()
        deposit = summary[summary["statement_type"] == "deposit"].copy()

        min_date = summary["date"].min() if "date" in summary.columns else None
        max_date = summary["date"].max() if "date" in summary.columns else None

        total_date = (max_date-min_date).days
        total_withdraw = round(abs(withdraw["amount"].sum()), 2) if not withdraw.empty else 0.0
        total_deposit = round(deposit["amount"].sum(), 2) if not deposit.empty else 0.0

        return {
            "row_count": int(len(summary)),
            "date_range": {
                "start": None if pd.isna(min_date) else str(min_date.date()),
                "end": None if pd.isna(max_date) else str(max_date.date()),
            },
            "total_withdraw": total_withdraw,
            "30 days withdraw avg": thirty_days_avg(total_withdraw, total_date),
            "total_deposit": total_deposit,
            "30 days deposit avg": thirty_days_avg(total_deposit, total_date),
            "net_change": round(summary["amount"].sum(), 2),
        }
    


def generate_bank_statement_summary(
    question: str = "Generate a bank statement report.",
    history: list[dict] | None = None,
) -> str:
    history = history or []
    bank_analyer = BankStatementAnalyzer()
    summary = bank_analyer.summarize_statement_data()

    if summary["row_count"] == 0:
        return "I couldn't find any bank statement rows in Google Sheets yet."

    context = f"""
You are generating a bank statement report from Google Sheets data.

Dataset summary:
- Row count: {summary["row_count"]}
- Date range: {summary["date_range"]}
- Total withdraw: {summary["total_withdraw"]}
- 30 days withdraw avgerage: {summary["30 days withdraw avg"]}
- Total deposit: {summary["total_deposit"]}
- 30 days withdraw avgerage: {summary["30 days deposit avg"]}
- Net change: {summary["net_change"]}

Write a concise bank statement style report with:
1. Overall activity summary
2. Cash flow / debit-credit summary
3. Notable large transactions
4. Recent activity
5. Any data-quality caveats if fields are missing or sparse

Use only the provided data. Be concrete and numeric.
"""

    augmented_history = list(history)
    augmented_history.append({"role": "assistant", "content": context})
    return call_model(question, augmented_history)
