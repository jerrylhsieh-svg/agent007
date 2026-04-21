import io
import re
from typing import Any
from abc import ABC, abstractmethod
import pdfplumber

from agent.models.pdf_models import BankStatementRow, TransactionRow


class BasePdfParser(ABC):
    document_type = "unknown"
    date_re = re.compile(
    r"^(?P<date>\d{1,2}/\d{1,2}(?:/\d{2,4})?|\d{4}-\d{2}-\d{2}|[A-Z][a-z]{2}\s+\d{1,2})$"
)

    def _build_base_result(self) -> dict[str, Any]:
        return {
            "pages": [],
            "tables": [],
            "transactions": [],
            "statements": [],
            "full_text": "",
            "quality": {},
        }

    def parse(self, file_bytes: bytes) -> dict[str, Any]:
        result = self._build_base_result()

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                self.process_page(result, page_number, page, page_text)

        return result
    
    def _is_date_token(self, value: str) -> bool:
        return bool(self.date_re.match(value.strip()))
    
    def _parse_amount(self, raw: str) -> float | None:
        cleaned = raw.strip().replace("$", "").replace(",", "")
        negative = False

        if cleaned.startswith("(") and cleaned.endswith(")"):
            negative = True
            cleaned = cleaned[1:-1]

        if cleaned.endswith("-"):
            negative = True
            cleaned = cleaned[:-1]

        value = float(cleaned)

        return -value if negative else value
    
    def _normalize_mmdd(self, value: str, statement_period: tuple[int, int, int, int]) -> str:

        start_month, start_year, _end_month, end_year = statement_period
        month_str, day_str = value[:5].split("/")
        month = int(month_str)
        day = int(day_str)

        if start_year != end_year:
            year = start_year if month >= start_month else end_year
        else:
            year = end_year

        return f"{year:04d}-{month:02d}-{day:02d}"
    
    def _normalize_date_value(self, value: str | None, statement_period: tuple[int, int, int, int] | None) -> str | None:
        if not value or statement_period is None:
            return value
        return self._normalize_mmdd(value, statement_period)
    
    @abstractmethod
    def process_page(self, result: dict[str, Any], page_number: int, page, page_text: str) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def _extract_statement_years(self, text: str | None) -> tuple[int, int, int, int] | None:
        raise NotImplementedError
    
    @abstractmethod
    def _normalize_date(
        self,
        record: TransactionRow | BankStatementRow = None,
        statement_period: tuple[int, int, int, int] | None = None,
    ) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def _update_section(self, current_section: str | None, line: str) -> str | None:
        raise NotImplementedError