from __future__ import annotations

from uuid import uuid4

from fastapi import BackgroundTasks, File, HTTPException, UploadFile

from agent.services.google_sheets import append_data, build_gsheet_rows
from agent.services.constants_and_dependencies import GSHEET_NAME, GSHEET_STATEMENT_TAB, GSHEET_TRANSACTIONS_TAB, STATEMENT_HEADERS, TRANSACTION_HEADERS
from agent.services.labeling.labeling_job_service import create_labeling_job, run_labeling_job
from agent.services.parser.pdf_parser import extract_pdf_content


async def extract_pdf_service(background_tasks: BackgroundTasks, file: UploadFile):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    extracted, doc_tpye = extract_pdf_content(file_bytes)

    if doc_tpye == "BOA_bank":
        worksheet_name=GSHEET_STATEMENT_TAB
        headers=STATEMENT_HEADERS
    else:
        worksheet_name=GSHEET_TRANSACTIONS_TAB
        headers=TRANSACTION_HEADERS

    rows = build_gsheet_rows(
        data=extracted["data"],
        fields=headers,
    )
    job = create_labeling_job(extracted["data"])
    background_tasks.add_task(
        run_labeling_job,
        job.id,
        extracted["data"],
        worksheet_name,
    )

    gsheet_status = "skipped"
    gsheet_error = None
    try:
        append_data(
            spreadsheet_name=GSHEET_NAME,
            worksheet_name=worksheet_name,
            rows=rows,
            headers=headers
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