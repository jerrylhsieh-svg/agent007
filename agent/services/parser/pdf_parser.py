from dataclasses import asdict
from datetime import datetime
import io
import re
from typing import Any, Literal
import pdfplumber

from agent.models.pdf_models import BankStatementRow, TransactionRow


DATE_RE = re.compile(
    r"^(?P<date>\d{1,2}/\d{1,2}(?:/\d{2,4})?|\d{4}-\d{2}-\d{2}|[A-Z][a-z]{2}\s+\d{1,2})$"
)


def _is_date_token(value: str) -> bool:
    return bool(DATE_RE.match(value.strip()))


def _parse_amount(raw: str) -> float | None:
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


def _extract_statement_years(text: str | None) -> tuple[int, int, int, int] | None:
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


def _normalize_mmdd(value: str, statement_period: tuple[int, int, int, int]) -> str:

    start_month, start_year, _end_month, end_year = statement_period
    month_str, day_str = value[:5].split("/")
    month = int(month_str)
    day = int(day_str)

    if start_year != end_year:
        year = start_year if month >= start_month else end_year
    else:
        year = end_year

    return f"{year:04d}-{month:02d}-{day:02d}"


def _normalize_date_value(value: str | None, statement_period: tuple[int, int, int, int] | None) -> str | None:
    if not value or statement_period is None:
        return value
    return _normalize_mmdd(value, statement_period)


def _normalize_date(
    *,
    transaction_record: TransactionRow | None = None,
    bank_record: BankStatementRow | None = None,
    statement_period: tuple[int, int, int, int] | None = None,
) -> None:
    if transaction_record is not None:
        transaction_record.transaction_date = _normalize_date_value(
            transaction_record.transaction_date,
            statement_period,
        )
        transaction_record.posting_date = _normalize_date_value(
            transaction_record.posting_date,
            statement_period,
        )

    if bank_record is not None:
        bank_record.date = _normalize_date_value(bank_record.date, statement_period)


def _build_base_result() -> dict[str, Any]:
    return {
        "pages": [],
        "tables": [],
        "transactions": [],
        "statements": [],
        "full_text": "",
        "quality": {},
    }


def _update_section(current_section: str | None, line: str) -> str | None:
    if line == "Purchases and Adjustments":
        return "credit_card_transaction"
    if line.startswith("TOTAL PURCHASES AND ADJUSTMENTS FOR THIS PERIOD"):
        return None

    if line == "Deposits and other additions":
        return "deposit"
    if line.startswith("Total deposits and other additions"):
        return None

    if line == "Withdrawals and other subtractions":
        return "withdraw"
    if line.startswith("Total withdrawals and other subtractions"):
        return None

    return current_section


def _parse_credit_card_transaction(line: str) -> TransactionRow | None:
    parts = line.split()
    if len(parts) < 5:
        return None

    if not _is_date_token(parts[0]) or not _is_date_token(parts[1]):
        return None

    return TransactionRow(
        transaction_date=parts[0],
        posting_date=parts[1],
        description=" ".join(parts[2:-2]),
        reference_number=int(parts[-2]),
        amount=float(parts[-1]),
        raw_line=line,
    )


def _parse_bank_statement_line(
    line: str,
    statement_type: Literal["deposit", "withdraw"],
) -> BankStatementRow | None:
    parts = line.split()
    if len(parts) < 3:
        return None

    if not _is_date_token(parts[0]):
        return None

    return BankStatementRow(
        date=parts[0],
        description=" ".join(parts[1:-1]),
        statement_type=statement_type,
        amount=_parse_amount(parts[-1]),
        raw_line=line,
    )


def _parse_statement_line(
    line: str,
    current_section: str | None,
) -> TransactionRow | BankStatementRow | None:
    if current_section == "credit_card_transaction":
        return _parse_credit_card_transaction(line)
    if current_section == "deposit":
        return _parse_bank_statement_line(line, "deposit")
    if current_section == "withdraw":
        return _parse_bank_statement_line(line, "withdraw")
    return None


def _extract_transactions_from_page(page_text: str) -> tuple[list[TransactionRow], list[BankStatementRow]]:
    current_section: str | None = None
    transactions: list[TransactionRow] = []
    statements: list[BankStatementRow] = []

    for raw_line in page_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        current_section = _update_section(current_section, line)
        parsed = _parse_statement_line(line, current_section)

        if parsed is None:
            continue

        if isinstance(parsed, TransactionRow):
            transactions.append(parsed)
        else:
            statements.append(parsed)

    return transactions, statements


def _extract_tables(page: pdfplumber.page.Page, page_number: int) -> list[dict[str, Any]]:
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


def _process_page(page_number: int, page: pdfplumber.page.Page) -> dict[str, Any]:
    page_text = page.extract_text() or ""
    transactions, statements = _extract_transactions_from_page(page_text)

    return {
        "page_text": page_text,
        "page": {
            "page_number": page_number,
            "text": page_text,
        },
        "tables": _extract_tables(page, page_number),
        "transactions": transactions,
        "statements": statements,
    }


def _normalize_records(
    transactions: list[TransactionRow],
    statements: list[BankStatementRow],
    full_text: str,
) -> None:
    statement_period = _extract_statement_years(full_text)

    for row in transactions:
        _normalize_date(transaction_record=row, statement_period=statement_period)

    for statement_row in statements:
        _normalize_date(bank_record=statement_row, statement_period=statement_period)


def _build_quality_metrics(transactions: list[TransactionRow]) -> dict[str, Any]:
    valid_amounts = sum(1 for row in transactions if row.amount is not None)

    return {
        "transaction_count": len(transactions),
        "valid_amount_ratio": round(valid_amounts / len(transactions), 3) if transactions else 0.0,
        "parser": "pdfplumber_layout_v2",
    }


def extract_pdf_content(file_bytes: bytes) -> dict[str, Any]:
    result = _build_base_result()

    full_text_parts: list[str] = []
    all_transactions: list[TransactionRow] = []
    all_statements: list[BankStatementRow] = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_result = _process_page(page_number, page)

            full_text_parts.append(f"\n--- Page {page_number} ---\n{page_result['page_text']}")
            all_transactions.extend(page_result["transactions"])
            all_statements.extend(page_result["statements"])
            result["pages"].append(page_result["page"])
            result["tables"].extend(page_result["tables"])

    result["full_text"] = "\n".join(full_text_parts)
    _normalize_records(all_transactions, all_statements, result["full_text"])
    result["transactions"] = [asdict(row) for row in all_transactions]
    result["statements"] = [asdict(row) for row in all_statements]
    result["quality"] = _build_quality_metrics(all_transactions)

    return result