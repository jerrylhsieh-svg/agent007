

from agent.services.parser.base_pdf_parser import BasePdfParser


class BOABankPdfParser(BasePdfParser):
    document_type = "bank_statement"