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
