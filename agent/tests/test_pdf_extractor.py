from __future__ import annotations

import io
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from agent.services import pdf_extractor
from agent.services.parser import pdf_parser


def make_upload_file(
    filename: str = "statement.pdf",
    content: bytes = b"%PDF-1.4 fake pdf bytes",
    content_type: str = "application/pdf",
) -> UploadFile:
    file_obj = io.BytesIO(content)
    return UploadFile(filename=filename, file=file_obj, headers=Headers({"content-type": content_type}))


def test_parse_amount_handles_positive_negative_and_invalid():
    assert pdf_parser._parse_amount("$1,234.56") == 1234.56
    assert pdf_parser._parse_amount("(123.45)") == -123.45
    assert pdf_parser._parse_amount("-99.01") == -99.01
    with pytest.raises(AttributeError):
        pdf_parser._parse_amount(None)
    with pytest.raises(ValueError):
        pdf_parser._parse_amount("not-a-number")


def test_extract_pdf_content_builds_expected_result_shape():
    fake_page = Mock()
    fake_page.extract_text.return_value = "page one text"
    fake_page.extract_tables.return_value = [[["Date", "Description", "Amount"]]]

    fake_row = pdf_parser.TransactionRow(
        transaction_date="2025-01-15",
        posting_date="2025-01-15",
        description="Coffee Shop",
        reference_number=2134,
        amount=4.50,
        raw_line="01/15/2025 Coffee Shop $4.50 $100.00",
    )

    fake_pdf = SimpleNamespace(pages=[fake_page])

    class FakePdfContext:
        def __enter__(self):
            return fake_pdf

        def __exit__(self, exc_type, exc, tb):
            return False

    with patch("agent.services.parser.pdf_parser.pdfplumber.open", return_value=FakePdfContext()), \
         patch("agent.services.parser.pdf_parser._extract_transactions_from_page", return_value=([fake_row], [])), \
         patch("agent.services.parser.pdf_parser._extract_statement_years", return_value=(1,2025,2,2025)), \
         patch("agent.services.parser.pdf_parser._normalize_mmdd", return_value=('2025-01-15')):

        result = pdf_parser.extract_pdf_content(b"fake-pdf-bytes")

    assert len(result["tables"]) == 1
    assert len(result["transactions"]) == 1
    assert result["quality"]["transaction_count"] == 1
    assert result["quality"]["valid_amount_ratio"] == 1.0
    assert "page one text" in result["full_text"]



@pytest.mark.asyncio
async def test_extract_pdf_service_rejects_non_pdf():
    file = make_upload_file(filename="bad.txt", content=b"hello", content_type="text/plain")

    with pytest.raises(HTTPException) as exc:
        await pdf_extractor.extract_pdf_service(file)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Only PDF files are supported."


@pytest.mark.asyncio
async def test_extract_pdf_service_rejects_empty_pdf():
    file = make_upload_file(filename="empty.pdf", content=b"", content_type="application/pdf")

    with pytest.raises(HTTPException) as exc:
        await pdf_extractor.extract_pdf_service(file)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Uploaded file is empty."


@pytest.mark.asyncio
async def test_extract_pdf_service_returns_summary_and_saves_json(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_extractor, "UPLOAD_DIR", tmp_path)

    extracted_payload = {
        "pages": [{"page_number": 1, "text": "hello", "diagnostics": {}}],
        "tables": [{"page_number": 1, "table_index": 1, "rows": [["a"]]}],
        "transactions": [{"date": "2025-01-15", "amount": 4.5}],
        "statements": [],
        "full_text": "hello",
        "quality": {"transaction_count": 1},
    }

    file = make_upload_file()

    with patch("agent.services.pdf_extractor.extract_pdf_content", return_value=extracted_payload), \
        patch("agent.services.pdf_extractor.append_data", return_value=(None, None)):
        result = await pdf_extractor.extract_pdf_service(file)

    assert result["filename"] == "statement.pdf"
    assert result["page_count"] == 1
    assert result["table_count"] == 1
    assert result["transaction_count"] == 1
    assert result["message"] == "PDF parsed with layout-based bank statement heuristics."

    saved_file = tmp_path / "statement.pdf.json"
    assert saved_file.exists()
    assert json.loads(saved_file.read_text()) == extracted_payload
