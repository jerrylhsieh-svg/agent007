from datetime import datetime
import re
from dateutil.parser import parse

from agent.services.constants_and_dependencies import DATE_RE, MONTH_LOOKUP, STATEMENT_PERIOD_RE  


def is_date_token(value: str, date_re=DATE_RE) -> bool:
        return bool(date_re.match(value.strip()))

def parse_month(value: str) -> int:
    value = value.strip().lower().rstrip(".")

    if value.isdigit():
        month = int(value)
        if 1 <= month <= 12:
            return month
        raise ValueError(f"Invalid month: {value}")

    if value not in MONTH_LOOKUP:
        raise ValueError(f"Invalid month: {value}")

    return MONTH_LOOKUP[value]
    
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
    
    parsed = parse(value)

    if parsed is None: raise ValueError(f"not able to normalize date {value}")

    if start_year != end_year:
        year = start_year if parsed.month >= start_month else end_year
    else:
        year = end_year

    return f"{year:04d}-{parsed.strftime("%m")}-{parsed.strftime("%d")}"

def extract_statement_years(text: str | None) -> tuple[int, int, int, int] | None:

    if not text:
        return None

    match = STATEMENT_PERIOD_RE.search(text)
    if not match:
        return None

    try:
        start_month = parse_month(match.group("start_month"))
        start_day = int(match.group("start_day"))
        start_year_raw = match.group("start_year")

        end_month = parse_month(match.group("end_month"))
        end_day = int(match.group("end_day"))
        end_year = int(match.group("end_year"))

        if start_year_raw:
            start_year = int(start_year_raw)
        else:
            if start_month > end_month:
                start_year = end_year - 1
            else:
                start_year = end_year

        datetime(start_year, start_month, start_day)
        datetime(end_year, end_month, end_day)

        return start_month, start_year, end_month, end_year

    except ValueError:
        return None


def is_account_number(value: str) -> bool:
    return value.isdigit() and len(value) == 4
