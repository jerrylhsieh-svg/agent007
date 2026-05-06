from __future__ import annotations

from typing import Any

from agent.services.analyzer.base_financial_analyzer import BaseFinancialAnalyzer
from agent.services.constants_and_dependencies import GSHEET_STATEMENT_TAB
from agent.services.helper import thirty_days_avg


class BankStatementAnalyzer(BaseFinancialAnalyzer):
    worksheet_name = GSHEET_STATEMENT_TAB

    def summarize(self) -> dict[str, Any]:
        working = self.df

        withdraw = working[working["amount"] < 0].copy()
        deposit = working[working["amount"] >= 0].copy()

        total_withdraw = round(abs(float(withdraw["amount"].sum())), 2) if not withdraw.empty else 0.0
        total_deposit = round(float(deposit["amount"].sum()), 2) if not deposit.empty else 0.0

        return {
            "row_count": int(len(working)),
            "date_range": self.get_date_range(working),
            "total_withdraw": total_withdraw,
            "30_days_withdraw_avg": thirty_days_avg(total_withdraw, self.total_days),
            "total_deposit": total_deposit,
            "30_days_deposit_avg": thirty_days_avg(total_deposit, self.total_days),
            "net_change": round(float(working["amount"].sum()), 2),
        }

    def summarize_withdraw(self) -> dict[str, Any]:
        withdraw = self.df[self.df["statement_type"] == "withdraw"].copy()
        desc = withdraw["description"].fillna("").str.lower()

        card_payment = withdraw[desc.str.contains("card", na=False)]
        investment = withdraw[desc.str.contains("robinhood", na=False)]
        other_withdraw = withdraw[
            ~desc.str.contains("card", na=False)
            & ~desc.str.contains("robinhood", na=False)
        ]

        total_card_payment = round(float(card_payment["amount"].sum()), 2)
        total_investment = round(float(investment["amount"].sum()), 2)
        total_other = round(float(other_withdraw["amount"].sum()), 2)

        return {
            "row_count": int(len(withdraw)),
            "card_payment_count": int(len(card_payment)),
            "card_payment_amount": total_card_payment,
            "30_days_card_payment_avg": thirty_days_avg(total_card_payment, self.total_days),
            "investment_count": int(len(investment)),
            "investment_amount": total_investment,
            "30_days_investment_avg": thirty_days_avg(total_investment, self.total_days),
            "other_withdraw_count": int(len(other_withdraw)),
            "other_withdraw_amount": total_other,
        }

    def build_summary_context(self, summary: dict[str, Any]) -> str:

        return f"""
You are generating a bank statement report from Google Sheets data.

Dataset summary:
- Row count: {summary["row_count"]}
- Date range: {summary["date_range"]}
- Total withdraw: {summary["total_withdraw"]}
- 30-day withdraw average: {summary["30_days_withdraw_avg"]}
- Total deposit: {summary["total_deposit"]}
- 30-day deposit average: {summary["30_days_deposit_avg"]}
- Net change: {summary["net_change"]}

Write a concise bank statement style report with:
1. Overall activity summary
2. Cash flow / debit-credit summary
3. Notable patterns in withdraws
4. Recent activity
5. Any data-quality caveats if fields are missing or sparse

Use only the provided data. Be concrete and numeric.
""".strip()
    

    def build_withdraw_context(self, withdraw_breakdown: dict[str, Any]) -> str:

        return f"""
You are generating a bank statement report from Google Sheets data.

Withdraw breakdown:
- Card payment count: {withdraw_breakdown["card_payment_count"]}
- Card payment amount: {withdraw_breakdown["card_payment_amount"]}
- 30-day card payment average: {withdraw_breakdown["30_days_card_payment_avg"]}
- Investment count: {withdraw_breakdown["investment_count"]}
- Investment amount: {withdraw_breakdown["investment_amount"]}
- 30-day investment average: {withdraw_breakdown["30_days_investment_avg"]}
- Other withdraw count: {withdraw_breakdown["other_withdraw_count"]}
- Other withdraw amount: {withdraw_breakdown["other_withdraw_amount"]}

Write a concise bank statement style report with:
1. Overall activity summary
2. Cash flow / debit-credit summary
3. Notable patterns in withdraws
4. Recent activity
5. Any data-quality caveats if fields are missing or sparse

Use only the provided data. Be concrete and numeric.
""".strip()


def generate_bank_statement_summary(
    question: str = "Generate a bank statement report.",
    history: list[dict] | None = None,
) -> str:
    analyzer = BankStatementAnalyzer()
    summary = analyzer.summarize()

    if summary["row_count"] == 0:
        return "I couldn't find any bank statement rows in Google Sheets yet."

    context = analyzer.build_summary_context(summary)
    return analyzer.llm_answer(question=question, history=history, context=context)


def generate_bank_withdraw_summary(
    question: str = "Generate a bank statement report.",
    history: list[dict] | None = None,
) -> str:
    analyzer = BankStatementAnalyzer()
    withdraw = analyzer.summarize_withdraw()

    if withdraw["row_count"] == 0:
        return "I couldn't find any bank statement rows in Google Sheets yet."

    context = analyzer.build_withdraw_context(withdraw)
    return analyzer.llm_answer(question=question, history=history, context=context)