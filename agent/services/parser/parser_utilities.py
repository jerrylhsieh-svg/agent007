from datetime import datetime
import re
from typing import Literal

from agent.models.pdf_models import LineSchema, TransactionRow

date_re = re.compile(
        r"^(?P<date>\d{1,2}/\d{1,2}(?:/\d{2,4})?|\d{4}-\d{2}-\d{2}|[A-Z][a-z]{2}\s+\d{1,2})$"
    )

def is_date_token(value: str, date_re=date_re) -> bool:
        return bool(date_re.match(value.strip()))
    
def parse_amount(raw: str) -> float:
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

def normalize_date_value(value: str | None, statement_period: tuple[int, int, int, int] | None) -> str | None:
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

def extract_statement_years(text: str | None) -> tuple[int, int, int, int] | None:
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

def parse_boa_credit(parts: list[str]):
    if not (
        is_date_token(parts[0])
        and is_date_token(parts[1])
        and is_account_number(parts[-2])
        and is_account_number(parts[-3])
    ):
        return None

    return TransactionRow(
        date=parts[0],
        description=" ".join(parts[2:-3]),
        amount=parse_amount(parts[-1]),
    )

def is_account_number(value: str) -> bool:
    return value.isdigit() and len(value) == 4
