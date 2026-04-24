from typing import List, Literal

from agent.models.pdf_models import BankStatementRow, TransactionRow
from agent.services.parser.base_pdf_parser import BasePdfParser


class BOABankPdfParser(BasePdfParser):
    
    def _extract_from_page(
        self,
        page: str,
    ) -> List:
        data = []
        for raw_line in page.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line == "Deposits and other additions":
                self.statement_type =  "deposit"
            elif line == "Withdrawals and other subtractions":
                 self.statement_type = "withdraw"
            parts = line.split()

            if len(parts) >= 3 and self._is_date_token(parts[0]):
                if self.current is not None:
                    self.current.description = " ".join(self.current.description.split())
                    data.append(self.current)

                    self.current = BankStatementRow(
                        date=parts[0],
                        description=" ".join(parts[1:-1]),
                        statement_type=self.statement_type,
                        amount=self._parse_amount(parts[-1]),
                    )
                elif line.startswith("Total deposits and other additions") \
                    or line.startswith("Total withdrawals and other subtractions"):
                    data.append(self.current)
                    self.current = None
                else:
                    if self.current is not None:
                        self.current.description += " " + line
                        continue
                    self.current = BankStatementRow(
                        date=parts[0],
                        description=" ".join(parts[1:-1]),
                        statement_type=self.statement_type,
                        amount=self._parse_amount(parts[-1]),
                    )
        return data
