from agent.db.data_classes.pdf_models import LineSchema
from agent.services.parser.base_pdf_parser import BasePdfParser


class GenericPdfParser(BasePdfParser):

    schema = LineSchema(
        name="date_description_amount",
        min_parts=3,
        end_markers=[],
        credit=True,
    )

    def __init__(self):
        super().__init__()
        self.credit = True
