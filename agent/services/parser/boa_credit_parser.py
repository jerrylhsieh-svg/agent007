from agent.db.data_classes.pdf_models import FinancialRecordRow, LineSchema
from agent.services.parser.base_pdf_parser import BasePdfParser
from agent.services.parser.parser_utilities import is_account_number, parse_amount


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
        
        parsed_date = self._extract_date_prefix(line)

        if parsed_date is None:
            return None

        date, rest = parsed_date

        if self.schema.name == "date_description_amount":
            return self._parse_date_description_amount(date, rest)

        if self.schema.name == "transaction_posting_description_ref_account_amount_total":
            return self._parse_boa_credit(rest)

        return None
    
    def _parse_boa_credit(self, rest: str):
        parts = rest.split()
        if not (
            is_account_number(parts[-2])
            and is_account_number(parts[-3])
        ):
            return None

        return FinancialRecordRow(
            date=parts[0],
            description=" ".join(parts[2:-3]),
            amount=parse_amount(parts[-1]),
        )
