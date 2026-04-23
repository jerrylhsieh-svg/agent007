from dataclasses import asdict
import io
from typing import Any

import pdfplumber

from agent.services.parser.boa_bank_parser import BOABankPdfParser
from agent.services.parser.boa_credit_parser import BOACreditPdfParser

def determine_pdf_type(line: str, pdf_info: dict[str, Any]) -> None:
    if pdf_info["bank"] is None:
        if "Bank of America" in line:
            pdf_info["bank"] = "BOA"
        elif "Bilt Cards" in line:
            pdf_info["bank"] = "Bilt"

    if pdf_info["credit"] is None:
        if "your statement" in line.lower():
            pdf_info["credit"] = False
        elif "minimum payment due" in line.lower():
            pdf_info["credit"] = True


def detect_pdf_info(pdf: pdfplumber.PDF) -> str:
    pdf_info: dict[str, Any] = {"bank": None, "credit": None}

    for page in pdf.pages:
        if pdf_info["bank"] is not None and pdf_info["credit"] is not None:
            break

        page_text = page.extract_text() or ""
        for raw_line in page_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            determine_pdf_type(line, pdf_info)

            if pdf_info["bank"] is not None and pdf_info["credit"] is not None:
                suffix = "credit" if pdf_info["credit"] else "bank"
                return f"{pdf_info["bank"]}_{suffix}"

    raise ValueError("pdf info not found")


def build_parser(doc_tpye: str) -> BOACreditPdfParser | BOABankPdfParser:

    if doc_tpye == "BOA_credit":
        return BOACreditPdfParser()
    return BOABankPdfParser()


def parse_pages(
    pdf: pdfplumber.PDF,
    pdf_parser: BOACreditPdfParser | BOABankPdfParser,
) -> tuple[str, list[Any]]:
    full_text_parts: list[str] = []
    data: list[Any] = []

    for page_number, page in enumerate(pdf.pages):
        page_result = pdf_parser.process_page(page_number, page)
        full_text_parts.append(
            f"\n--- Page {page_number} ---\n{page_result['full_text']}"
        )
        data.extend(page_result["data"])

    return "\n".join(full_text_parts), data


def extract_pdf_content(file_bytes: bytes) -> tuple[dict[str, Any], str]:
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        doc_tpye = detect_pdf_info(pdf)
        pdf_parser = build_parser(doc_tpye)
        full_text, data = parse_pages(pdf, pdf_parser)

    pdf_parser.normalize_records(data, full_text)

    return {"full_text": full_text,"data": [asdict(row) for row in data]}, doc_tpye
    