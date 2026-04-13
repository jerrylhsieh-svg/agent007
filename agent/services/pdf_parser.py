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


def _normalize_date(record: TransactionRow | None, statement_period: tuple[int, int, int, int] | None = None) -> str | None:
    td = date_parser.parse(record.transaction_date, fuzzy=False, default=date_parser.parse("2000-01-01"))
    pd = date_parser.parse(record.posting_date, fuzzy=False, default=date_parser.parse("2000-01-01"))
    start_month, start_year, end_month, end_year = statement_period
    td = td.replace(year=start_year)  if td.month == start_month else td.replace(year=end_year)
    pd = pd.replace(year=start_year)  if pd.month == start_month else pd.replace(year=end_year)
    record.transaction_date = td.date().isoformat()
    record.posting_date = pd.date().isoformat()



def _extract_transactions_from_page(page) -> tuple[list[TransactionRow], dict[str, Any]]:
    credit_card_transaction = False
    bank_account = False
    rows: list[TransactionRow] = []
    for line in page.split("\n"):
        if line == "Purchases and Adjustments":
            credit_card_transaction = True
            continue
        elif line.startswith("TOTAL PURCHASES AND ADJUSTMENTS FOR THIS PERIOD"):
            credit_card_transaction = False

        if credit_card_transaction:
            line_split = line.split(" ")
            rows.append(
                TransactionRow(
                    transaction_date=line_split[0],
                    posting_date=line_split[1],
                    description=" ".join(line_split[2:-2]),
                    reference_number=int(line_split[-2]),
                    amount=float(line_split[-1]),
                    raw_line=line,
                )
            )


    return rows

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

            rows = _extract_transactions_from_page(page_text)
            all_rows.extend(rows)

            result["pages"].append(
                {
                    "page_number": page_number,
                    "text": page_text,
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
        _normalize_date(row, statement_period)
    result["transactions"] = [asdict(r) for r in all_rows]

    valid_amounts = sum(1 for r in all_rows if r.amount is not None)

    result["quality"] = {
        "transaction_count": len(all_rows),
        "valid_amount_ratio": round(valid_amounts / len(all_rows), 3) if all_rows else 0.0,
        "parser": "pdfplumber_layout_v2",
    }

    return result