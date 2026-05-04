import re

from agent.models.pdf_models import LineSchema
from agent.services.parser.base_pdf_parser import BasePdfParser


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
        columns=["date", "description", "amount"],
        min_parts=3,
        start_markers=[],
        end_markers=["Total new charges in this period"],
        credit=True,
    )

    def __init__(self):
        super().__init__()
        self.credit = True
