from datetime import datetime
import re
from typing import Any, Literal
from abc import ABC, abstractmethod
import pdfplumber

from agent.models.pdf_models import BankStatementRow, TransactionRow


class BasePdfParser(ABC):
    date_re = re.compile(
        r"^(?P<date>\d{1,2}/\d{1,2}(?:/\d{2,4})?|\d{4}-\d{2}-\d{2}|[A-Z][a-z]{2}\s+\d{1,2})$"
    )

    def __init__(self):
        self.current = None
        self.statement_type: Literal["deposit", "withdraw"] | None = None
        self.credit = False

    def build_base_result(self) -> dict[str, Any]:
        return {
            "pages": [],
            "tables": [],
            "data": [],
            "full_text": "",
        }

    
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

    def _ignore_neg(self) -> bool:
        if self.credit and self.current.amount<0:
            return True
        return False
    
    def _normalize_date_value(self, value: str | None, statement_period: tuple[int, int, int, int] | None) -> str | None:
        if not value or statement_period is None or re.search(r"\b\d{4}-\d{2}-\d{2}\b", value):
            return value
        start_month, start_year, _end_month, end_year = statement_period
        parsed = None
        for fmt in ("%m/%d", "%b %d", "%B %d"):
            try:
                parsed = datetime.strptime(value[:5].strip(","), fmt)
            except ValueError:
                continue
        if parsed is None: raise ValueError(f"not able to normalize date {value}")

        if start_year != end_year:
            year = start_year if parsed.month >= start_month else end_year
        else:
            year = end_year

        return f"{year:04d}-{parsed.strftime("%m")}-{parsed.strftime("%d")}"
    
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
    
    def normalize_records(
        self,
        data: list[TransactionRow | BankStatementRow],
        full_text: str,
    ) -> None:
        statement_period = self._extract_statement_years(full_text)

        for row in data:
            self._normalize_date_value(value=row.date, statement_period=statement_period)
    
    @abstractmethod
    def _extract_from_page(self, page: str) -> list:
        raise NotImplementedError