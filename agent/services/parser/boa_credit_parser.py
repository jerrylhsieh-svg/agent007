from typing import List

from agent.models.pdf_models import BankStatementRow, LineSchema, TransactionRow
from agent.services.parser.base_pdf_parser import BasePdfParser
from agent.services.parser.parser_utilities import is_account_number, is_date_token, parse_amount


class BOACreditPdfParser(BasePdfParser):

    schema = LineSchema(
        name="transaction_posting_description_ref_account_amount_total",
        record_type="transaction",
        columns=[
            "transaction_date",
            "posting_date",
            "description",
            "reference_number",
            "account_number",
            "amount",
            "total",
        ],
        min_parts=6,
        start_markers=[],
        end_markers=["TOTAL PURCHASES AND ADJUSTMENTS FOR THIS PERIOD"],
        credit=True,
    )

    def __init__(self):
        super().__init__()
        self.credit = True

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
        data: list[TransactionRow | BankStatementRow | None] = []
        for raw_line in page.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 6 and is_date_token(parts[0]) and is_date_token(parts[1])\
                and is_account_number(parts[-2]) and is_account_number(parts[-3]):
                if line.startswith("TOTAL PURCHASES AND ADJUSTMENTS FOR THIS PERIOD"):
                    if not self._ignore_neg():
                        data.append(self.current) 
                    break
                if self.current is not None:
                    self.current.description = " ".join(self.current.description.split())
                    if not self._ignore_neg():
                        data.append(self.current)

                self.current = TransactionRow(
                    date=parts[0],
                    description=" ".join(parts[2:-3]),
                    amount=parse_amount(parts[-1]),
                )
            else:
                if self.current is not None:
                    self.current.description += " " + line

        return data
