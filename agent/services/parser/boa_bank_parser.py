from typing import List

from agent.models.pdf_models import BankStatementRow, LineSchema, TransactionRow
from agent.services.parser.base_pdf_parser import BasePdfParser
from agent.services.parser.parser_utilities import is_date_token, parse_amount


class BOABankPdfParser(BasePdfParser):

    schema = LineSchema(
        name="date_description_amount",
        columns=["date", "description", "amount"],
        min_parts=3,
        start_markers=[],
        end_markers=[
            "Total deposits and other additions",
            "Total withdrawals and other subtractions",
        ],
        statement_type_markers={
            "Deposits and other additions": "deposit",
            "Withdrawals and other subtractions": "withdraw",
        },
    )
    
    def _extract_from_page(
        self,
        page: str,
    ) -> List:
        data: list[TransactionRow | BankStatementRow | None] = []
        for raw_line in page.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line == "Deposits and other additions":
                self.statement_type =  "deposit"
            elif line == "Withdrawals and other subtractions":
                self.statement_type = "withdraw"
            parts = line.split()

            if len(parts) >= 3 and is_date_token(parts[0]):
                if self.current is not None:
                    self.current.description = " ".join(self.current.description.split())
                    data.append(self.current)

                if self.statement_type is None:
                    raise ValueError(f"statement_type not defined")

                self.current = BankStatementRow(
                    date=parts[0],
                    description=" ".join(parts[1:-1]),
                    statement_type=self.statement_type,
                    amount=parse_amount(parts[-1]),
                )
            elif line.startswith("Total deposits and other additions") \
                or line.startswith("Total withdrawals and other subtractions"):
                data.append(self.current)
                self.current = None
            else:
                if self.current is not None:
                    self.current.description += " " + line
                    
        return data
