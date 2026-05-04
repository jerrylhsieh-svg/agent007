from typing import Any, Literal
from abc import ABC
import pdfplumber

from agent.models.pdf_models import BankStatementRow, LineSchema, TransactionRow
from agent.services.parser.parser_utilities import extract_statement_years, is_date_token, normalize_date_value, parse_amount


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
        data: list[TransactionRow | BankStatementRow],
        full_text: str,
    ) -> None:
        statement_period = extract_statement_years(full_text)
        for row in data:
            row.date = normalize_date_value(value=row.date, statement_period=statement_period)
    
    def parse_page(self, page: str) -> list[TransactionRow | BankStatementRow]:
        data: list[TransactionRow | BankStatementRow] = []

        for raw_line in page.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if self._is_end_line(line):
                self._flush_current(data)
                self.current = None
                continue

            self._update_statement_type(line)

            parsed = self._parse_transaction_line(line)

            if parsed:
                self._flush_current(data)
                self.current = parsed
            elif self.current is not None:
                self.current.description += f" {line}"

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

        if self.schema.credit is False:
            if self.statement_type is None:
                raise ValueError("statement_type not detected")

            return BankStatementRow(
                date=date,
                description=description,
                statement_type=self.statement_type,
                amount=amount,
            )

        return TransactionRow(
            date=date,
            description=description,
            amount=amount,
        )
    
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
