from dataclasses import asdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
import io
import re
from typing import Any
import fitz  
from dateutil import parser as date_parser
import pdfplumber

from agent.models.pdf_models import TransactionRow


DATE_RE = re.compile(
    r"^(?P<date>\d{1,2}/\d{1,2}(?:/\d{2,4})?|\d{4}-\d{2}-\d{2}|[A-Z][a-z]{2}\s+\d{1,2})$"
)

AMOUNT_RE = re.compile(
    r"^[\-\(]?\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?\)?$"
)

def _looks_scanned(file_bytes: bytes) -> bool:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        text_chars = 0
        for page in doc:
            text = page.get_text("text") or ""
            text_chars += len(text.strip())
        return text_chars < 40
    finally:
        doc.close()


def _group_words_into_lines(words: list[dict], y_tolerance: float = 3.0) -> list[list[dict]]:
    if not words:
        return []

    words = sorted(words, key=lambda w: (round(w["top"], 1), w["x0"]))
    lines: list[list[dict]] = []
    current: list[dict] = []
    current_top = None

    for w in words:
        if current_top is None:
            current = [w]
            current_top = w["top"]
            continue

        if abs(w["top"] - current_top) <= y_tolerance:
            current.append(w)
        else:
            lines.append(sorted(current, key=lambda x: x["x0"]))
            current = [w]
            current_top = w["top"]

    if current:
        lines.append(sorted(current, key=lambda x: x["x0"]))

    return lines


def _parse_amount(value: str | None) -> float | None:
    if not value:
        return None
    raw = value.strip().replace("$", "").replace(",", "")
    negative = False

    if raw.startswith("(") and raw.endswith(")"):
        negative = True
        raw = raw[1:-1]
    if raw.startswith("-"):
        negative = True
        raw = raw[1:]

    try:
        amt = Decimal(raw)
        return float(-amt if negative else amt)
    except (InvalidOperation, ValueError):
        return None


def _extract_statement_years(statement_period: str | None) -> tuple[int, int] | None:
    if not statement_period:
        return None

    match = re.search(
        r"([A-Za-z]+)\s+\d{1,2}\s*-\s*([A-Za-z]+)\s+\d{1,2},\s*(\d{4})",
        statement_period,
    )
    if not match:
        return None

    start_month_name, end_month_name, end_year_str = match.groups()
    end_year = int(end_year_str)

    start_month = datetime.strptime(start_month_name, "%B").month
    end_month = datetime.strptime(end_month_name, "%B").month

    start_year = end_year - 1 if start_month > end_month else end_year
    return start_month, start_year, end_month, end_year


def _apply_statement_year(date_value: str | None, statement_period: tuple[int, int, int, int] | None) -> str | None:
    if not date_value or not statement_period:
        return date_value
    dt = date_parser.parse(date_value, fuzzy=False, default=date_parser.parse("2000-01-01"))
    start_month, start_year, end_month, end_year = statement_period

    if dt.month == start_month:
        dt = dt.replace(year=start_year)
    elif dt.month == end_month:
        dt = dt.replace(year=end_year)

    return dt.date().isoformat()


def _line_to_text(line: list[dict]) -> str:
    return " ".join(w["text"] for w in line).strip()


def _extract_transactions_from_page(page, page_number: int) -> tuple[list[TransactionRow], dict[str, Any]]:
    words_raw = page.extract_words(
        keep_blank_chars=False,
        use_text_flow=True,
        extra_attrs=[]
    )

    words = [
        {"text": w["text"], "x0": w["x0"], "x1": w["x1"], "top": w["top"], "bottom": w["bottom"]}
        for w in words_raw
    ]

    lines = _group_words_into_lines(words)

    rows: list[TransactionRow] = []
    non_transaction_lines: list[str] = []

    for line in lines:
        line_text = _line_to_text(line)
        if not line_text:
            continue

        # Heuristic: first token is often date
        first = line[0]["text"]
        date_token = first if DATE_RE.match(first) else None

        # Right-most numeric tokens are usually amount / balance
        numeric_tokens = [w for w in line if AMOUNT_RE.match(w["text"])]
        amount = None
        balance = None
        description = line_text

        if date_token:
            # Remove date token from description
            remaining = [w for w in line[1:]]

            # Pick last numeric as balance, second last as amount when present
            if len(numeric_tokens) >= 2:
                amount = _parse_amount(numeric_tokens[-2]["text"])
                balance = _parse_amount(numeric_tokens[-1]["text"])
            elif len(numeric_tokens) == 1:
                amount = _parse_amount(numeric_tokens[-1]["text"])

            numeric_texts = {w["text"] for w in numeric_tokens}
            desc_tokens = [w["text"] for w in remaining if w["text"] not in numeric_texts]
            description = " ".join(desc_tokens).strip()

            rows.append(
                TransactionRow(
                    page_number=page_number,
                    date=date_token,
                    description=description,
                    amount=amount,
                    balance=balance,
                    raw_line=line_text,
                )
            )
        else:
            non_transaction_lines.append(line_text)

    # Merge wrapped description lines into previous transaction
    merged_rows: list[TransactionRow] = []
    for row in rows:
        if merged_rows and (not row.date) and row.description:
            merged_rows[-1].description += " " + row.description
            merged_rows[-1].raw_line += " " + row.raw_line
        else:
            merged_rows.append(row)

    diagnostics = {
        "line_count": len(lines),
        "transaction_count": len(merged_rows),
        "non_transaction_lines_sample": non_transaction_lines[:15],
    }
    return merged_rows, diagnostics

def extract_pdf_content(file_bytes: bytes) -> dict[str, Any]:
    scanned = _looks_scanned(file_bytes)

    result: dict[str, Any] = {
        "document_type": "bank_statement_candidate",
        "is_scanned": scanned,
        "needs_ocr": scanned,
        "pages": [],
        "tables": [],
        "transactions": [],
        "full_text": "",
        "quality": {},
    }

    full_text_parts: list[str] = []
    all_rows: list[TransactionRow] = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            full_text_parts.append(f"\n--- Page {page_number} ---\n{page_text}")

            rows, diagnostics = _extract_transactions_from_page(page, page_number)
            all_rows.extend(rows)

            result["pages"].append(
                {
                    "page_number": page_number,
                    "text": page_text,
                    "diagnostics": diagnostics,
                }
            )

            page_tables = page.extract_tables()
            for table_index, table in enumerate(page_tables, start=1):
                result["tables"].append(
                    {
                        "page_number": page_number,
                        "table_index": table_index,
                        "rows": table,
                    }
                )

    result["full_text"] = "\n".join(full_text_parts)
    statement_period = _extract_statement_years(result["full_text"])
    for row in all_rows:
        row.date = _apply_statement_year(row.date, statement_period)
    result["transactions"] = [asdict(r) for r in all_rows]

    valid_dates = sum(1 for r in all_rows if r.date)
    valid_amounts = sum(1 for r in all_rows if r.amount is not None)

    result["quality"] = {
        "transaction_count": len(all_rows),
        "valid_date_ratio": round(valid_dates / len(all_rows), 3) if all_rows else 0.0,
        "valid_amount_ratio": round(valid_amounts / len(all_rows), 3) if all_rows else 0.0,
        "parser": "pdfplumber_layout_v2",
    }

    return result