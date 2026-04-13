from __future__ import annotations

import io
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, UploadFile

from agent.services import pdf_extractor, pdf_parser


def make_upload_file(
    filename: str = "statement.pdf",
    content: bytes = b"%PDF-1.4 fake pdf bytes",
    content_type: str = "application/pdf",
) -> UploadFile:
    file_obj = io.BytesIO(content)
    return UploadFile(filename=filename, file=file_obj, headers={"content-type": content_type})


def test_parse_amount_handles_positive_negative_and_invalid():
    assert pdf_parser._parse_amount("$1,234.56") == 1234.56
    assert pdf_parser._parse_amount("(123.45)") == -123.45
    assert pdf_parser._parse_amount("-99.01") == -99.01
    assert pdf_parser._parse_amount(None) is None
    assert pdf_parser._parse_amount("not-a-number") is None


def test_normalize_date_handles_multiple_formats_and_invalid():
    assert pdf_parser._normalize_date("1/15/2025") == "2025-01-15"
    assert pdf_parser._normalize_date("2025-02-03") == "2025-02-03"
    assert pdf_parser._normalize_date("Jan 8") == "2000-01-08"


def test_group_words_into_lines_groups_by_top_and_sorts_by_x0():
    words = [
        {"text": "B", "x0": 50, "x1": 60, "top": 10.2, "bottom": 12},
        {"text": "A", "x0": 10, "x1": 20, "top": 10.0, "bottom": 12},
        {"text": "C", "x0": 15, "x1": 25, "top": 30.0, "bottom": 32},
    ]

    lines = pdf_parser._group_words_into_lines(words, y_tolerance=3.0)

    assert len(lines) == 2
    assert [w["text"] for w in lines[0]] == ["A", "B"]
    assert [w["text"] for w in lines[1]] == ["C"]


def test_extract_transactions_from_page_parses_date_description_amount_balance():
    page = Mock()
    page.extract_words.return_value = [
        {"text": "01/15/2025", "x0": 0, "x1": 10, "top": 10, "bottom": 12},
        {"text": "Coffee", "x0": 20, "x1": 35, "top": 10, "bottom": 12},
        {"text": "Shop", "x0": 36, "x1": 50, "top": 10, "bottom": 12},
        {"text": "$4.50", "x0": 80, "x1": 90, "top": 10, "bottom": 12},
        {"text": "$100.00", "x0": 100, "x1": 115, "top": 10, "bottom": 12},
    ]

    rows, diagnostics = pdf_parser._extract_transactions_from_page(page, page_number=1)

    assert len(rows) == 1
    row = rows[0]
    assert row.page_number == 1
    assert row.date == "01/15/2025"
    assert row.description == "Coffee Shop"
    assert row.amount == 4.50
    assert row.balance == 100.00
    assert diagnostics["transaction_count"] == 1


def test_extract_transactions_from_page_keeps_non_transaction_lines_in_diagnostics():
    page = Mock()
    page.extract_words.return_value = [
        {"text": "Statement", "x0": 0, "x1": 20, "top": 10, "bottom": 12},
        {"text": "Summary", "x0": 25, "x1": 45, "top": 10, "bottom": 12},
    ]

    rows, diagnostics = pdf_parser._extract_transactions_from_page(page, page_number=1)

    assert rows == []
    assert diagnostics["transaction_count"] == 0
    assert diagnostics["non_transaction_lines_sample"] == ["Statement Summary"]


def test_extract_pdf_content_builds_expected_result_shape():
    fake_page = Mock()
    fake_page.extract_text.return_value = "page one text"
    fake_page.extract_tables.return_value = [[["Date", "Description", "Amount"]]]

    fake_row = pdf_parser.TransactionRow(
        page_number=1,
        date="2025-01-15",
        description="Coffee Shop",
        amount=4.50,
        balance=100.00,
        raw_line="01/15/2025 Coffee Shop $4.50 $100.00",
    )

    fake_pdf = SimpleNamespace(pages=[fake_page])

    class FakePdfContext:
        def __enter__(self):
            return fake_pdf

        def __exit__(self, exc_type, exc, tb):
            return False

    with patch("agent.services.pdf_parser._looks_scanned", return_value=False), \
         patch("agent.services.pdf_parser.pdfplumber.open", return_value=FakePdfContext()), \
         patch("agent.services.pdf_parser._extract_transactions_from_page", return_value=([fake_row], {"line_count": 1, "transaction_count": 1, "non_transaction_lines_sample": []})):

        result = pdf_parser.extract_pdf_content(b"fake-pdf-bytes")

    assert result["document_type"] == "bank_statement_candidate"
    assert result["is_scanned"] is False
    assert result["needs_ocr"] is False
    assert len(result["pages"]) == 1
    assert len(result["tables"]) == 1
    assert len(result["transactions"]) == 1
    assert result["quality"]["transaction_count"] == 1
    assert result["quality"]["valid_date_ratio"] == 1.0
    assert result["quality"]["valid_amount_ratio"] == 1.0
    assert "page one text" in result["full_text"]


def test_looks_scanned_returns_true_when_text_is_minimal():
    fake_page = Mock()
    fake_page.get_text.return_value = "x"

    fake_doc = Mock()
    fake_doc.__iter__ = Mock(return_value=iter([fake_page]))
    fake_doc.close = Mock()

    with patch("agent.services.pdf_parser.fitz.open", return_value=fake_doc):
        assert pdf_parser._looks_scanned(b"fake") is True

    fake_doc.close.assert_called_once()


def test_looks_scanned_returns_false_when_text_is_present():
    fake_page = Mock()
    fake_page.get_text.return_value = "This page has enough text to not be considered scanned."

    fake_doc = Mock()
    fake_doc.__iter__ = Mock(return_value=iter([fake_page]))
    fake_doc.close = Mock()

    with patch("agent.services.pdf_parser.fitz.open", return_value=fake_doc):
        assert pdf_parser._looks_scanned(b"fake") is False


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
        "needs_ocr": False,
        "is_scanned": False,
        "document_type": "bank_statement_candidate",
        "full_text": "hello",
        "quality": {"transaction_count": 1},
    }

    file = make_upload_file()

    with patch("agent.services.pdf_extractor.extract_pdf_content", return_value=extracted_payload), \
        patch("agent.services.pdf_extractor.append_transactions", return_value=None):
        result = await pdf_extractor.extract_pdf_service(file)

    assert result["filename"] == "statement.pdf"
    assert result["page_count"] == 1
    assert result["table_count"] == 1
    assert result["transaction_count"] == 1
    assert result["message"] == "PDF parsed with layout-based bank statement heuristics."

    saved_file = tmp_path / "statement.pdf.json"
    assert saved_file.exists()
    assert json.loads(saved_file.read_text()) == extracted_payload


@pytest.mark.asyncio
async def test_extract_pdf_service_returns_ocr_message_when_needed(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_extractor, "UPLOAD_DIR", tmp_path)

    extracted_payload = {
        "pages": [],
        "tables": [],
        "transactions": [],
        "needs_ocr": True,
        "is_scanned": True,
        "document_type": "bank_statement_candidate",
        "full_text": "",
        "quality": {"transaction_count": 0},
    }

    file = make_upload_file()

    with patch("agent.services.pdf_extractor.extract_pdf_content", return_value=extracted_payload), \
        patch("agent.services.pdf_extractor.append_transactions", return_value=None):
        result = await pdf_extractor.extract_pdf_service(file)

    assert result["message"] == "PDF looks scanned; OCR should run before reliable bank statement extraction."