import re
from typing import List

from agent.models.pdf_models import BankStatementRow, BiltTransactionRow, TransactionRow
from agent.services.parser.base_pdf_parser import BasePdfParser


class BiltCreditPdfParser(BasePdfParser):
    DATE_AMOUNT_RE = re.compile(
        r"""
        ^(?P<date>[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})   
        \s+
        (?P<description>.*?)                         
        \s+
        \$(?P<amount>\d[\d,]*\.\d{2})$               
        """,
        re.VERBOSE,
    )

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
        if line == "jerry hsieh Bilt Blue Card":
            return "credit_card_transaction"
        if line.startswith("Total new charges in this period"):
            return None

        return current_section
    
    def _extract_from_page(
        self,
        page: str,
        data: List=[],
    ) -> List:
        for raw_line in page.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            match = self.DATE_AMOUNT_RE.match(line)
            if match:
                if self.current is not None:
                    self.current.description = " ".join(self.current.description.split())
                    data.append(self.current)

                    self.current = BiltTransactionRow(
                        date=match.group("date"),
                        description=match.group("description"),
                        amount=self._parse_amount(match.group("amount")),
                    )
            elif line.startswith("Total new charges in this period"):
                data.append(self.current)
                self.current = None
            else:
                if self.current is not None:
                    self.current.description += " " + line
                    continue
                
                self.current = BiltTransactionRow(
                        date=match.group("date"),
                        description=match.group("description"),
                        amount=self._parse_amount(match.group("amount")),
                    )
                

        return data
