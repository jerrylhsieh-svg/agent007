from __future__ import annotations

from uuid import uuid4

from fastapi import File, HTTPException, UploadFile

from agent.services.google_sheets import _build_gsheet_rows, append_data
from agent.services.constants_and_dependencies import GSHEET_NAME, GSHEET_STATEMENT_TAB, GSHEET_TRANSACTIONS_TAB
from agent.services.parser.pdf_parser import extract_pdf_content


async def extract_pdf_service(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    extracted, doc_tpye = extract_pdf_content(file_bytes)

    upload_id = uuid4().hex[:12]
    rows = _build_gsheet_rows(
        filename=file.filename,
        upload_id=upload_id,
        data=extracted["data"],
        doc_tpye=doc_tpye,
    )

    gsheet_status = "skipped"
    gsheet_error = None
    try:
        if doc_tpye == "BOA_bank":
            append_data(
                spreadsheet_name=GSHEET_NAME,
                worksheet_name=GSHEET_STATEMENT_TAB,
                rows=rows,
                data_type="statement"
            )
        else:
            append_data(
                spreadsheet_name=GSHEET_NAME,
                worksheet_name=GSHEET_TRANSACTIONS_TAB,
                rows=rows,
                data_type="transaction"
            )
        gsheet_status = "uploaded"
    except Exception as exc:
        gsheet_status = "failed"
        gsheet_error = str(exc)
        raise HTTPException(status_code=500, detail="Failed to write to Gsheet")

    message = "PDF parsed with layout-based bank statement heuristics."

    return {
        "filename": file.filename,
        "row_count": len(extracted["data"]),
        "message": message,
        "data": extracted,
        "gsheet_status": gsheet_status,
        "gsheet_error": gsheet_error,
    }