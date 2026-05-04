import re
from typing import List

from agent.models.pdf_models import BankStatementRow, LineSchema, TransactionRow
from agent.services.parser.base_pdf_parser import BasePdfParser
from agent.services.parser.parser_utilities import parse_amount


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

    schema = LineSchema(
        name="date_description_amount",
        record_type="transaction",
        columns=["date", "description", "amount"],
        min_parts=3,
        start_markers=[],
        end_markers=["Total new charges in this period"],
        credit=True,
    )

    def __init__(self):
        super().__init__()
        self.credit = True
    
    def _extract_from_page(
        self,
        page: str,
    ) -> List:
        data: list[TransactionRow | BankStatementRow | None] = []
        for raw_line in page.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            match = self.DATE_AMOUNT_RE.match(line)
            if match:
                if self.current is not None:
                    self.current.description = " ".join(self.current.description.split())
                    if not self._ignore_neg():
                        data.append(self.current)

                self.current = TransactionRow(
                    date=match.group("date"),
                    description=match.group("description"),
                    amount=parse_amount(match.group("amount")),
                )
            elif line.startswith("Total new charges in this period"):
                if not self._ignore_neg():
                    data.append(self.current)
                self.current = None
            else:
                if self.current is not None:
                    self.current.description += " " + line

        return data
