from typing import List

from agent.models.pdf_models import BankStatementRow, TransactionRow
from agent.services.parser.base_pdf_parser import BasePdfParser


class BOACreditPdfParser(BasePdfParser):

    def _is_account_number(self, num):
        try:
            int(num)
        except:
            return False
        return len(num) == 4
    
    def _extract_from_page(
        self,
        page: str,
    ) -> List:
        data = []
        for raw_line in page.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 6 and self._is_date_token(parts[0]) and self._is_date_token(parts[1])\
                and self._is_account_number(parts[-2]) and self._is_account_number(parts[-3]):
                if line.startswith("TOTAL PURCHASES AND ADJUSTMENTS FOR THIS PERIOD"):
                    data.append(self.current)
                    break
                if self.current is not None:
                    self.current.description = " ".join(self.current.description.split())
                    data.append(self.current)

                self.current = TransactionRow(
                    date=parts[0],
                    posting_date=parts[1],
                    description=" ".join(parts[2:-3]),
                    reference_number=int(parts[-3]),
                    amount=self._parse_amount(parts[-1]),
                )
            else:
                if self.current is not None:
                    self.current.description += " " + line

        return data
