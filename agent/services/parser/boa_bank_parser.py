from agent.db.data_classes.pdf_models import LineSchema
from agent.services.parser.base_pdf_parser import BasePdfParser


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
