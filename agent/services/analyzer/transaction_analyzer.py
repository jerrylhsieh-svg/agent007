from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from agent.services.analyzer.base_financial_analyzer import BaseFinancialAnalyzer
from agent.services.helper import thirty_days_avg


class CreditCardTransactionAnalyzer(BaseFinancialAnalyzer):
    file_type = "transaction"

    def summarize(self) -> dict[str, Any]:
        working = self.df

        total_spend = round(float(working["amount"].sum()), 2) if not working.empty else 0.0

        merchant_counter: Counter[str] = Counter()
        if "label" in working.columns:
            for l in working["label"].fillna(""):
                if l:
                    merchant_counter[l] += 1

        return {
            "row_count": int(len(working)),
            "date_range": self.get_date_range(working),
            "total_spend": total_spend,
            "30_days_spend_avg": thirty_days_avg(total_spend, self.total_days),
            "top_spending_categories": merchant_counter.most_common(5),
        }

    def build_summary_context(self, summary: dict[str, Any]) -> str:
        return f"""
You are analyzing personal transaction data stored in Google Sheets.

Dataset summary:
- Row count: {summary["row_count"]}
- Date range: {summary["date_range"]}
- Total spend: {summary["total_spend"]}
- 30-day spend average: {summary["30_days_spend_avg"]}
- Top spending categories: {summary["top_spending_categories"]}

Answer the user's question using only this transaction context.
If the data is insufficient, say what is missing.
Be concrete and numeric where possible.
""".strip()


def generate_credit_card_summary(
    question: str,
    db: Session,
    history: list[dict] | None = None,
) -> str:
    analyzer = CreditCardTransactionAnalyzer(db)
    summary = analyzer.summarize()

    if summary["row_count"] == 0:
        return "I couldn't find any transaction rows in the database."

    context = analyzer.build_summary_context(summary)
    return analyzer.llm_answer(question=question, history=history, context=context)