from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi import File, HTTPException, UploadFile

from agent.services.google_sheets import _build_gsheet_rows, append_transactions
from agent.services.pdf_parser import extract_pdf_content

UPLOAD_DIR = Path("/tmp/agent_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
GSHEET_NAME = "Sheet1"
GSHEET_TRANSACTIONS_TAB = "transactions"


async def extract_pdf_service(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    extracted = extract_pdf_content(file_bytes)

    saved_path = UPLOAD_DIR / f"{file.filename}.json"
    saved_path.write_text(json.dumps(extracted, ensure_ascii=False, indent=2))

    upload_id = uuid4().hex[:12]
    gsheet_rows = _build_gsheet_rows(
        filename=file.filename,
        upload_id=upload_id,
        transactions=extracted["transactions"],
    )

    gsheet_status = "skipped"
    gsheet_error = None
    try:
        append_transactions(
            spreadsheet_name=GSHEET_NAME,
            worksheet_name=GSHEET_TRANSACTIONS_TAB,
            rows=gsheet_rows,
        )
        gsheet_status = "uploaded"
    except Exception as exc:
        gsheet_status = "failed"
        gsheet_error = str(exc)

    message = (
        "PDF looks scanned; OCR should run before reliable bank statement extraction."
        if extracted["needs_ocr"]
        else "PDF parsed with layout-based bank statement heuristics."
    )

    return {
        "filename": file.filename,
        "page_count": len(extracted["pages"]),
        "table_count": len(extracted["tables"]),
        "transaction_count": len(extracted["transactions"]),
        "message": message,
        "data": extracted,
        "saved_to": str(saved_path),
        "gsheet_status": gsheet_status,
        "gsheet_error": gsheet_error,
    }