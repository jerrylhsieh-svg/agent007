from datetime import datetime
import io
import re
from typing import Any
from abc import ABC, abstractmethod
import pdfplumber

from agent.models.pdf_models import BankStatementRow, TransactionRow


class BasePdfParser(ABC):
    date_re = re.compile(
    r"^(?P<date>\d{1,2}/\d{1,2}(?:/\d{2,4})?|\d{4}-\d{2}-\d{2}|[A-Z][a-z]{2}\s+\d{1,2})$"
)

    def build_base_result(self) -> dict[str, Any]:
        return {
            "pages": [],
            "tables": [],
            "data": [],
            "full_text": "",
        }

    def parse(self, file_bytes: bytes) -> dict[str, Any]:
        result = self.build_base_result()

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                self.process_page(page_number, page)

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
    
    def _extract_statement_years(self, text: str | None) -> tuple[int, int, int, int] | None:
        if not text:
            return None

        match = re.search(
            r"([A-Za-z]+)\s+(\d{1,2})(?:,\s*(\d{4}))?\s*(?:to|-)\s*([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})",
            text,
        )
        if not match:
            return None

        start_month_name, _start_day, start_year_str, end_month_name, _end_day, end_year_str = match.groups()
        end_year = int(end_year_str)

        start_month = datetime.strptime(start_month_name, "%B").month
        end_month = datetime.strptime(end_month_name, "%B").month

        if start_year_str:
            start_year = int(start_year_str)
        else:
            start_year = end_year - 1 if start_month > end_month else end_year

        return start_month, start_year, end_month, end_year
    
    def _extract_from_page(self, page_text: str) -> list:
        current_section: str | None = None
        data = []

        for raw_line in page_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            current_section = self._update_section(current_section, line)
            parsed = self._process_line(line, current_section)

            if parsed is None:
                continue

            data.append(parsed)

        return data
    
    def _extract_tables(self, page: pdfplumber.page.Page, page_number: int) -> list[dict[str, Any]]:
        tables: list[dict[str, Any]] = []

        for table_index, table in enumerate(page.extract_tables(), start=1):
            tables.append(
                {
                    "page_number": page_number,
                    "table_index": table_index,
                    "rows": table,
                }
            )

        return tables
    
    def process_page(self, page_number: int, page: pdfplumber.page.Page) -> dict[str, Any]:
        page_text = page.extract_text() or ""
        data = self._extract_from_page(page_text)

        return {
            "full_text": page_text,
            "page": {
                "page_number": page_number,
                "text": page_text,
            },
            "tables": self._extract_tables(page, page_number),
            "data": data,
        }
    
    def _normalize_records(
        self,
        data: list,
        full_text: str,
    ) -> None:
        statement_period = self._extract_statement_years(full_text)

        for row in data:
            self._normalize_date(record=row, statement_period=statement_period)
    
    @abstractmethod
    def _process_line(self, line: str, current_section: str | None,) -> TransactionRow | BankStatementRow | None:
        raise NotImplementedError
    
    @abstractmethod
    def _normalize_date(
        self,
        record: TransactionRow | BankStatementRow | None = None,
        statement_period: tuple[int, int, int, int] | None = None,
    ) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def _update_section(self, current_section: str | None, line: str) -> str | None:
        raise NotImplementedError