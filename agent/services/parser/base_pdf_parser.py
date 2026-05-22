from typing import Any, Literal
from abc import ABC
import pdfplumber

from agent.db.data_classes.pdf_models import LineSchema, FinancialRecordRow
from agent.services.parser.parser_utilities import extract_statement_years, is_date_token, normalize_date_value, parse_amount


class BasePdfParser(ABC):
    schema: LineSchema
    doc_type: str = "unknown"
    max_continuation_lines: int = 1

    def __init__(self):
        self.current: FinancialRecordRow | None = None
        self.continuation_count = 0
        self.statement_type: Literal["deposit", "withdraw"] | None = None
        self.credit = False

    @classmethod
    def can_parse(cls, doc_type: str) -> bool:
        return cls.doc_type == doc_type

    def build_base_result(self) -> dict[str, Any]:
        return {
            "pages": [],
            "tables": [],
            "data": [],
            "full_text": "",
        }
    
    def process_page(self, page_number: int, page: pdfplumber.page.Page, end_page: int) -> dict[str, Any]:
        page_text = page.extract_text() or ""
        data = self.parse_page(page_text)
        if page_number ==  end_page and self.current is not None:
            self._flush_current(data)

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
        data: list[FinancialRecordRow],
        full_text: str,
    ) -> None:
        statement_period = extract_statement_years(full_text)
        for row in data:
            row.date = normalize_date_value(value=row.date, statement_period=statement_period)
    
    def parse_page(self, page: str) -> list[FinancialRecordRow]:
        data: list[FinancialRecordRow] = []

        for raw_line in page.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if self._is_end_line(line):
                self._flush_current(data)
                self.current = None
                self.continuation_count = 0
                continue

            self._update_statement_type(line)

            parsed = self._parse_transaction_line(line)

            if parsed:
                self._flush_current(data)
                self.current = parsed
                self.continuation_count = 0

            elif self.current is not None and self.continuation_count < self.max_continuation_lines:
                self.current.description += f" {line}"
                self.continuation_count += 1

            elif self.current is not None:
                self._flush_current(data)
                self.current = None
                self.continuation_count = 0

        return data
    
    def _ignore_neg(self) -> bool:
        if self.credit and self.current and self.current.amount<0:
            return True
        return False
    
    def _flush_current(self, data: list):
        if self.current is None:
            return

        self.current.description = " ".join(self.current.description.split())

        if self.schema.credit and self.current.amount < 0:
            return

        data.append(self.current)

    def _is_end_line(self, line: str) -> bool:
        if not self.schema.end_markers:
            return False

        return any(line.startswith(marker) for marker in self.schema.end_markers)

    def _update_statement_type(self, line: str) -> None:
        if not self.schema.statement_type_markers:
            return

        for marker, statement_type in self.schema.statement_type_markers.items():
            if line == marker:
                self.statement_type = statement_type
    
    def _parse_date_description_amount(self, date: str, rest: str):
        parts = rest.split()
        amount = parse_amount(parts[-1])
        description = " ".join(parts[0:-1])

        return FinancialRecordRow(
            date=date,
            description=description,
            amount=amount,
        )
    
    def _parse_transaction_line(self, line: str):
        parts = line.split()

        if len(parts) < self.schema.min_parts:
            return None
        
        parsed_date = self._extract_date_prefix(line)
        parsed_amount = self._extract_amount(line)

        if parsed_date is None or not parsed_amount:
            return None

        date, rest = parsed_date

        if self.schema.name == "date_description_amount":
            return self._parse_date_description_amount(date, rest)

        return None
    
    def _extract_date_prefix(self, line: str) -> tuple[str, str] | None:
        tokens = line.split()

        max_date_tokens = min(4, len(tokens))

        for size in range(max_date_tokens, 0, -1):
            candidate = " ".join(tokens[:size])

            if is_date_token(candidate):
                rest = " ".join(tokens[size:]).strip()
                return candidate, rest

        return None
    
    def _extract_amount(self, line: str) -> bool:
        tokens = line.split()
        try:
            parse_amount(tokens[-1])
        except:
            return False
        return True
