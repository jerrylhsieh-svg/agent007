from __future__ import annotations

from typing import Any

import pandas as pd

from agent.services.call_model import call_model
from agent.services.google_sheets import read_transactions_df
from agent.services.gsheet_config import GSHEET_NAME, GSHEET_STATEMENT_TAB
from agent.services.helper import _safe_float



def _normalize_statement_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes likely bank-statement columns into a consistent shape:
    date, description, amount, statement_type, source_file
    """
    if df.empty:
        return df.copy()

    working = df.copy()

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

    return working


def _summarize_statement_data(df: pd.DataFrame) -> dict[str, Any]:
    working = _normalize_statement_df(df)

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

    working = working.dropna(subset=["amount"]).copy()

    debits = working[working["amount"] < 0].copy()
    credits = working[working["amount"] > 0].copy()

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

    largest_debits = []
    if not debits.empty:
        top_debits = debits.nsmallest(10, "amount")
        for _, row in top_debits.iterrows():
            largest_debits.append(
                {
                    "date": None if pd.isna(row.get("date")) else str(row["date"].date()),
                    "description": row.get("description"),
                    "amount": _safe_float(row.get("amount")),
                    "statement_type": row.get("statement_type"),
                    "source_file": row.get("source_file"),
                }
            )

    largest_credits = []
    if not credits.empty:
        top_credits = credits.nlargest(10, "amount")
        for _, row in top_credits.iterrows():
            largest_credits.append(
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
        "total_debits": round(abs(debits["amount"].sum()), 2) if not debits.empty else 0.0,
        "total_credits": round(credits["amount"].sum(), 2) if not credits.empty else 0.0,
        "net_change": round(working["amount"].sum(), 2),
        "largest_debits": largest_debits,
        "largest_credits": largest_credits,
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

    summary = _summarize_statement_data(df)

    if summary["row_count"] == 0:
        return "I couldn't find any bank statement rows in Google Sheets yet."

    context = f"""
You are generating a bank statement report from Google Sheets data.

Dataset summary:
- Row count: {summary["row_count"]}
- Date range: {summary["date_range"]}
- Total debits: {summary["total_debits"]}
- Total credits: {summary["total_credits"]}
- Net change: {summary["net_change"]}

Statement types:
{summary["statement_types"]}

Largest debits:
{summary["largest_debits"]}

Largest credits:
{summary["largest_credits"]}

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