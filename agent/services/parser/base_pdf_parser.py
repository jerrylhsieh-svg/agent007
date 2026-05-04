import re
from typing import Any, Literal
from abc import ABC, abstractmethod
import pdfplumber

from agent.models.pdf_models import BankStatementRow, LineSchema, TransactionRow
from agent.services.parser.parser_utilities import extract_statement_years, flush_current, is_end_line, normalize_date_value, parse_transaction_line, update_statement_type


class BasePdfParser(ABC):
    schema: LineSchema

    def __init__(self):
        self.current: BankStatementRow | TransactionRow | None = None
        self.statement_type: Literal["deposit", "withdraw"] | None = None
        self.credit = False

    def build_base_result(self) -> dict[str, Any]:
        return {
            "pages": [],
            "tables": [],
            "data": [],
            "full_text": "",
        }
    
    def process_page(self, page_number: int, page: pdfplumber.page.Page) -> dict[str, Any]:
        page_text = page.extract_text() or ""
        data = self._extract_from_page(page_text)

        return {
            "full_text": page_text,
            "page": {
                "page_number": page_number,
                "text": page_text,
            },
            "data": data,
        }
    
    def normalize_records(
        self,
        data: list[TransactionRow | BankStatementRow],
        full_text: str,
    ) -> None:
        statement_period = extract_statement_years(full_text)

        for row in data:
            normalize_date_value(value=row.date, statement_period=statement_period)
    
    def parse_page(self, page: str) -> list[TransactionRow | BankStatementRow]:
        data: list[TransactionRow | BankStatementRow] = []

        for raw_line in page.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if is_end_line(self.schema, line,):
                flush_current(data, self.current, self.schema)
                self.current = None
                continue

            update_statement_type(self.schema, line)

            parsed = parse_transaction_line(self.schema, line, self.statement_type)

            if parsed:
                flush_current(data, self.current, self.schema)
                self.current = parsed
            elif self.current is not None:
                self.current.description += " " + line

        return data
    
    @abstractmethod
    def _extract_from_page(self, page: str) -> list:
        raise NotImplementedError