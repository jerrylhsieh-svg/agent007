from typing import List

from agent.models.pdf_models import BankStatementRow, LineSchema, TransactionRow
from agent.services.parser.base_pdf_parser import BasePdfParser
from agent.services.parser.parser_utilities import is_account_number, is_date_token, parse_amount


class BOACreditPdfParser(BasePdfParser):

    schema = LineSchema(
        name="transaction_posting_description_ref_account_amount_total",
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
    
    def _parse_transaction_line(self, line: str):
        parts = line.split()

        if len(parts) < self.schema.min_parts:
            return None

        if self.schema.name == "date_description_amount":
            return self._parse_date_description_amount(parts)

        if self.schema.name == "transaction_posting_description_ref_account_amount_total":
            return self._parse_boa_credit(parts)

        return None
    
    def _parse_boa_credit(self, parts: list[str]):
        if not (
            is_date_token(parts[0])
            and is_date_token(parts[1])
            and is_account_number(parts[-2])
            and is_account_number(parts[-3])
        ):
            return None

        return TransactionRow(
            date=parts[0],
            description=" ".join(parts[2:-3]),
            amount=parse_amount(parts[-1]),
        )
