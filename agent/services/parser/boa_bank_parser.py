from agent.db.data_classes.pdf_models import LineSchema
from agent.services.parser.base_pdf_parser import BasePdfParser


class BOABankPdfParser(BasePdfParser):
    doc_type = "BOA_bank"

    schema = LineSchema(
        name="date_description_amount",
        min_parts=3,
        end_markers=[
            "Total deposits and other additions",
            "Total withdrawals and other subtractions",
        ],
        statement_type_markers={
            "Deposits and other additions": "deposit",
            "Withdrawals and other subtractions": "withdraw",
        },
    )
