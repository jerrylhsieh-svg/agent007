from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi import File, HTTPException, UploadFile

from agent.services.google_sheets import _build_gsheet_rows, append_data
from agent.services.gsheet_config import GSHEET_NAME, GSHEET_STATEMENT_TAB, GSHEET_TRANSACTIONS_TAB
from agent.services.pdf_parser import extract_pdf_content

UPLOAD_DIR = Path("/tmp/agent_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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
    transaction_rows, statement_row = _build_gsheet_rows(
        filename=file.filename,
        upload_id=upload_id,
        transactions=extracted["transactions"],
        statements=extracted["statements"],
    )

    gsheet_status = "skipped"
    gsheet_error = None
    try:
        if transaction_rows:
            append_data(
                spreadsheet_name=GSHEET_NAME,
                worksheet_name=GSHEET_TRANSACTIONS_TAB,
                rows=transaction_rows,
                data_type="transaction"
            )
        if statement_row:
            append_data(
                spreadsheet_name=GSHEET_NAME,
                worksheet_name=GSHEET_STATEMENT_TAB,
                rows=statement_row,
                data_type="statement"
            )
        gsheet_status = "uploaded"
    except Exception as exc:
        gsheet_status = "failed"
        gsheet_error = str(exc)
        raise HTTPException(status_code=500, detail="Failed to write to Gsheet")

    message = "PDF parsed with layout-based bank statement heuristics."

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