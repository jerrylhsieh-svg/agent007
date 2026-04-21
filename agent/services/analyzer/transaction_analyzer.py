from __future__ import annotations

from collections import Counter
from typing import Any

from agent.services.base_financial_analyzer import BaseFinancialAnalyzer
from agent.services.gsheet_config import GSHEET_TRANSACTIONS_TAB
from agent.services.helper import thirty_days_avg


class CreditCardTransactionAnalyzer(BaseFinancialAnalyzer):
    worksheet_name = GSHEET_TRANSACTIONS_TAB

    def summarize(self) -> dict[str, Any]:
        working = self.df
        expenses = working[working["amount"] >= 0].copy()

        total_spend = round(float(expenses["amount"].sum()), 2) if not expenses.empty else 0.0

        merchant_counter: Counter[str] = Counter()
        if "description" in expenses.columns:
            for desc in expenses["description"].fillna(""):
                normalized = " ".join(str(desc).strip().split())
                if normalized:
                    merchant_counter[normalized[:80]] += 1

        return {
            "row_count": int(len(working)),
            "date_range": self.get_date_range(working),
            "total_spend": total_spend,
            "30_days_spend_avg": thirty_days_avg(total_spend, self.total_days),
            "top_merchants": merchant_counter.most_common(5),
        }

    def build_summary_context(self, summary: dict[str, Any]) -> str:
        return f"""
You are analyzing personal transaction data stored in Google Sheets.

Dataset summary:
- Row count: {summary["row_count"]}
- Date range: {summary["date_range"]}
- Total spend: {summary["total_spend"]}
- 30-day spend average: {summary["30_days_spend_avg"]}
- Top merchants: {summary["top_merchants"]}

Answer the user's question using only this transaction context.
If the data is insufficient, say what is missing.
Be concrete and numeric where possible.
""".strip()


def generate_credit_card_summary(
    question: str,
    history: list[dict] | None = None,
) -> str:
    analyzer = CreditCardTransactionAnalyzer()
    summary = analyzer.summarize()

    if summary["row_count"] == 0:
        return "I couldn't find any transaction rows in Google Sheets yet."

    context = analyzer.build_summary_context(summary)
    return analyzer.llm_answer(question=question, history=history, context=context)