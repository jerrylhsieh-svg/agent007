from __future__ import annotations
from dataclasses import asdict

from fastapi import BackgroundTasks, Depends, HTTPException, UploadFile

from agent.db.session import get_db_session
from agent.learning_models.labeler import Labeler
from agent.repo.financial_record_repository import FinancialRecordRepository
from agent.services.labeling.labeling_job_service import create_labeling_job, run_transaction_labeling_job
from agent.services.parser.pdf_parser import extract_pdf_content


async def extract_pdf_service(background_tasks: BackgroundTasks, file: UploadFile):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    extracted, doc_tpye = extract_pdf_content(file_bytes)

    if doc_tpye == "BOA_bank":
        repo = FinancialRecordRepository(Depends(get_db_session), record_type="statement")
        labeler = Labeler(file_type="statement")
    else:
        repo = FinancialRecordRepository(Depends(get_db_session), record_type="transaction")
        labeler = Labeler(file_type="transaction")

    try:
        repo.insert_many(extracted["data"])
    except:
        raise HTTPException(status_code=500, detail="Failed to write into database")

    message = "PDF parsed with layout-based bank statement heuristics."

    job = create_labeling_job(extracted["data"])
    background_tasks.add_task(
        run_transaction_labeling_job,
        job.id,
        [asdict(row) for row in extracted["data"]],
        labeler,
    )

    return {
        "filename": file.filename,
        "row_count": len(extracted["data"]),
        "message": message,
        "data": extracted,
    }