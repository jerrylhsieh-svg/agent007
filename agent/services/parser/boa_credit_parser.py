from typing import List

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
    
    def _extract_from_page(
        self,
        page: str,
        data: List = []
    ) -> List:
        for raw_line in page.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 5 and self._is_date_token(parts[0]) and self._is_date_token(parts[1]):
                if self.current is not None:
                    self.current.description = " ".join(self.current.description.split())
                    data.append(self.current)

                    self.current = TransactionRow(
                        transaction_date=parts[0],
                        posting_date=parts[1],
                        description=" ".join(parts[2:-2]),
                        reference_number=int(parts[-2]),
                        amount=self._parse_amount(parts[-1]),
                    )
                elif line.startswith("TOTAL PURCHASES AND ADJUSTMENTS FOR THIS PERIOD"):
                    data.append(self.current)
                    self.current = None
                else:
                    if self.current is not None:
                        self.current.description += " " + line
                        continue
                    self.current = TransactionRow(
                        transaction_date=parts[0],
                        posting_date=parts[1],
                        description=" ".join(parts[2:-2]),
                        reference_number=int(parts[-2]),
                        amount=self._parse_amount(parts[-1]),
                    )
        return data
