from __future__ import annotations

from typing import Any

import pandas as pd

from agent.services.call_model import call_model
from agent.services.google_sheets import read_transactions_df
from agent.services.gsheet_config import GSHEET_NAME, GSHEET_STATEMENT_TAB
from agent.services.helper import _safe_float

class BankStatementAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = self._normalize_statement_df(df)
        self._debits = None
        self._credits = None
        self._monthly_summary = None

    def _normalize_statement_df(self) -> pd.DataFrame:
        """
        Normalizes likely bank-statement columns into a consistent shape:
        date, description, amount, statement_type, source_file
        """
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


    def _summarize_statement_data(self) -> dict[str, Any]:
        working = self.df

        if working.empty or "amount" not in working.columns:
            return {
                "row_count": 0,
                "date_range": None,
                "total_debits": 0.0,
                "total_credits": 0.0,
                "net_change": 0.0,
                "largest_debits": [],
                "largest_credits": [],
                "statement_types": [],
                "recent_entries": [],
            }

        withdraw = working[working["statement_type"] == "withdraw"].copy()
        deposit = working[working["statement_type"] == "deposit"].copy()

        min_date = working["date"].min() if "date" in working.columns else None
        max_date = working["date"].max() if "date" in working.columns else None

        statement_types = []
        if "statement_type" in working.columns:
            counts = (
                working["statement_type"]
                .fillna("unknown")
                .astype(str)
                .value_counts()
                .reset_index()
            )
            counts.columns = ["statement_type", "count"]
            statement_types = counts.to_dict(orient="records")

        largest_withdraw = []
        if not withdraw.empty:
            top_withdraw = withdraw.nsmallest(10, "amount")
            for _, row in top_withdraw.iterrows():
                largest_withdraw.append(
                    {
                        "date": None if pd.isna(row.get("date")) else str(row["date"].date()),
                        "description": row.get("description"),
                        "amount": _safe_float(row.get("amount")),
                        "statement_type": row.get("statement_type"),
                        "source_file": row.get("source_file"),
                    }
                )

        largest_deposit = []
        if not deposit.empty:
            top_deposit = deposit.nlargest(10, "amount")
            for _, row in top_deposit.iterrows():
                largest_deposit.append(
                    {
                        "date": None if pd.isna(row.get("date")) else str(row["date"].date()),
                        "description": row.get("description"),
                        "amount": _safe_float(row.get("amount")),
                        "statement_type": row.get("statement_type"),
                        "source_file": row.get("source_file"),
                    }
                )

        recent_entries = []
        sort_cols = [c for c in ("date",) if c in working.columns]
        latest = (
            working.sort_values(sort_cols, ascending=False).head(20)
            if sort_cols
            else working.head(20)
        )
        for _, row in latest.iterrows():
            recent_entries.append(
                {
                    "date": None if pd.isna(row.get("date")) else str(row["date"].date()),
                    "description": row.get("description"),
                    "amount": _safe_float(row.get("amount")),
                    "statement_type": row.get("statement_type"),
                    "source_file": row.get("source_file"),
                }
            )

        return {
            "row_count": int(len(working)),
            "date_range": {
                "start": None if pd.isna(min_date) else str(min_date.date()),
                "end": None if pd.isna(max_date) else str(max_date.date()),
            },
            "total_withdraw": round(abs(withdraw["amount"].sum()), 2) if not withdraw.empty else 0.0,
            "total_deposit": round(deposit["amount"].sum(), 2) if not deposit.empty else 0.0,
            "net_change": round(working["amount"].sum(), 2),
            "largest_withdraw": largest_withdraw,
            "largest_deposit": largest_deposit,
            "statement_types": statement_types,
            "recent_entries": recent_entries,
        }


def generate_bank_statement_report(
    question: str = "Generate a bank statement report.",
    history: list[dict] | None = None,
) -> str:
    history = history or []

    df = read_transactions_df(
        spreadsheet_name=GSHEET_NAME,
        worksheet_name=GSHEET_STATEMENT_TAB,
    )

    analyzer = BankStatementAnalyzer(df)

    summary = analyzer._summarize_statement_data()

    if summary["row_count"] == 0:
        return "I couldn't find any bank statement rows in Google Sheets yet."

    context = f"""
You are generating a bank statement report from Google Sheets data.

Dataset summary:
- Row count: {summary["row_count"]}
- Date range: {summary["date_range"]}
- Total withdraw: {summary["total_withdraw"]}
- Total deposit: {summary["total_deposit"]}
- Net change: {summary["net_change"]}

Statement types:
{summary["statement_types"]}

Largest withdraw:
{summary["largest_withdraw"]}

Largest deposit:
{summary["largest_deposit"]}

Recent entries:
{summary["recent_entries"]}

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