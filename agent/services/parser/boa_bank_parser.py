

import io
from typing import Any, Literal

import pdfplumber

from agent.models.pdf_models import BankStatementRow, TransactionRow
from agent.services.parser.base_pdf_parser import BasePdfParser


class BOABankPdfParser(BasePdfParser):
    document_type = "bank_statement"

    def _normalize_date(
        self,
        bank_record: TransactionRow | BankStatementRow | None = None,
        statement_period: tuple[int, int, int, int] | None = None,
    ) -> None:
        if isinstance(bank_record, BankStatementRow):
            bank_record.date = self._normalize_date_value(bank_record.date, statement_period)

    def _update_section(self, current_section: str | None, line: str) -> str | None:
        if line == "Deposits and other additions":
            return "deposit"
        if line.startswith("Total deposits and other additions"):
            return None

        if line == "Withdrawals and other subtractions":
            return "withdraw"
        if line.startswith("Total withdrawals and other subtractions"):
            return None

        return current_section
    
    def _parse_bank_statement_line(self,
        line: str,
        statement_type: Literal["deposit", "withdraw"],
    ) -> BankStatementRow | None:
        parts = line.split()
        if len(parts) < 3:
            return None

        if not self._is_date_token(parts[0]):
            return None

        return BankStatementRow(
            date=parts[0],
            description=" ".join(parts[1:-1]),
            statement_type=statement_type,
            amount=self._parse_amount(parts[-1]),
            raw_line=line,
        )
    
    def _process_line(self, line: str, current_section: str | None,) -> BankStatementRow | None:
        if current_section == "deposit":
            return self._parse_bank_statement_line(line, "deposit")
        if current_section == "withdraw":
            return self._parse_bank_statement_line(line, "withdraw")
        return None
