from __future__ import annotations

import io
from unittest.mock import Mock, patch

import pytest
from fastapi import BackgroundTasks, HTTPException, UploadFile
from starlette.datastructures import Headers

from agent.models.labeling_job import LabelingJob
from agent.services import pdf_extractor
from agent.services.parser import pdf_parser

    
def make_upload_file(
    filename: str = "statement.pdf",
    content: bytes = b"%PDF-1.4 fake pdf bytes",
    content_type: str = "application/pdf",
) -> UploadFile:
    file_obj = io.BytesIO(content)
    return UploadFile(filename=filename, file=file_obj, headers=Headers({"content-type": content_type}))


def test_extract_pdf_content_builds_expected_result_shape():
    fake_row = Mock()
    fake_row_dict = {
        "date": "2025-01-15",
        "description": "test",
        "statement_type": "withdraw",
        "amount": 10.0,
        "raw_line": "01/15 test 10.0",
    }

    fake_parser = Mock()
    fake_parser.normalize_records.return_value = None

    class FakePdfContext:
        def __enter__(self):
            return fake_pdf

        def __exit__(self, exc_type, exc, tb):
            return False
    
    fake_pdf = FakePdfContext()

    with (
        patch("agent.services.parser.pdf_parser.pdfplumber.open", return_value=fake_pdf),
        patch("agent.services.parser.pdf_parser.detect_pdf_info", return_value="BOA_bank"),
        patch("agent.services.parser.pdf_parser.build_parser", return_value=fake_parser),
        patch(
            "agent.services.parser.pdf_parser.parse_pages",
            return_value=("full text", [fake_row]),
        ),
        patch("agent.services.parser.pdf_parser.asdict", return_value=fake_row_dict),
    ):
        result, doc_type = pdf_parser.extract_pdf_content(b"fake-pdf-bytes")

    fake_parser.normalize_records.assert_called_once_with([fake_row], "full text")
    assert doc_type == "BOA_bank"
    assert result == {
        "full_text": "full text",
        "data": [fake_row_dict],
    }



@pytest.mark.asyncio
async def test_extract_pdf_service_rejects_non_pdf():
    file = make_upload_file(filename="bad.txt", content=b"hello", content_type="text/plain")
    background_tasks = BackgroundTasks()

    with pytest.raises(HTTPException) as exc:
        await pdf_extractor.extract_pdf_service(background_tasks, file)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Only PDF files are supported."


@pytest.mark.asyncio
async def test_extract_pdf_service_rejects_empty_pdf():
    file = make_upload_file(filename="empty.pdf", content=b"", content_type="application/pdf")
    background_tasks = BackgroundTasks()

    with pytest.raises(HTTPException) as exc:
        await pdf_extractor.extract_pdf_service(background_tasks, file)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Uploaded file is empty."


@pytest.mark.asyncio
async def test_extract_pdf_service_returns_summary_and_saves_json():

    extracted_payload = (
        {
            "data": [{"date": "2025-01-15", "amount": 4.5}],
            "full_text": "hello",
        },
        "BOA_bank"
    )

    file = make_upload_file()
    background_tasks = BackgroundTasks()

    with patch("agent.services.pdf_extractor.extract_pdf_content", return_value=extracted_payload), \
        patch("agent.services.pdf_extractor.create_labeling_job", return_value=LabelingJob(id=1)), \
        patch("agent.services.pdf_extractor.append_data", return_value=(None, None)):
        result = await pdf_extractor.extract_pdf_service(background_tasks, file)

    assert result["filename"] == "statement.pdf"
    assert result["row_count"] == 1
    assert result["message"] == "PDF parsed with layout-based bank statement heuristics."
