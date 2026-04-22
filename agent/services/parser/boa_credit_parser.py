from agent.models.pdf_models import BankStatementRow, TransactionRow
from agent.services.parser.base_pdf_parser import BasePdfParser


class BOACreditPdfParser(BasePdfParser):
    def _normalize_date(
        self,
        record: TransactionRow | BankStatementRow | None = None,
        statement_period: tuple[int, int, int, int] | None = None,
    ) -> None:
        if isinstance(record, TransactionRow):
            record.transaction_date = self._normalize_date_value(
                record.transaction_date,
                statement_period,
            )
            record.posting_date = self._normalize_date_value(
                record.posting_date,
                statement_period,
            )

    def _update_section(self, current_section: str | None, line: str) -> str | None:
        if line == "Purchases and Adjustments":
            return "credit_card_transaction"
        if line.startswith("TOTAL PURCHASES AND ADJUSTMENTS FOR THIS PERIOD"):
            return None

        return current_section
    
    def _parse_credit_line(
        self,
        line: str,
    ) -> TransactionRow | None:
        parts = line.split()
        if len(parts) < 5:
            return None

        if not self._is_date_token(parts[0]) or not self._is_date_token(parts[1]):
            return None

        return TransactionRow(
            transaction_date=parts[0],
            posting_date=parts[1],
            description=" ".join(parts[2:-2]),
            reference_number=int(parts[-2]),
            amount=float(parts[-1]),
            raw_line=line,
        )
    
    def _process_line(self, line: str, current_section: str | None,) -> TransactionRow | None:
        if current_section == "credit_card_transaction":
            return self._parse_credit_line(line)
        return None
