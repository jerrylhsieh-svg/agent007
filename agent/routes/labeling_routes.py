from multiprocessing.resource_tracker import getfd

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from agent.services.constants_and_dependencies import labeling_store
from agent.services.labeling.labeled_csv_upload_service import LabeledCsvUploadService


router = APIRouter()


@router.get("/labeling-jobs/{job_id}")
def get_labeling_job(job_id: str):
    job = labeling_store.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Labeling job not found")

    return {
        "job_id": job.id,
        "status": job.status,
        "total_records": job.total_records,
        "processed_records": job.processed_records,
        "error_message": job.error_message,
    }


@router.get("/labeling-jobs/{job_id}/result")
def get_labeling_result(job_id: str):
    job = labeling_store.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Labeling job not found")

    if job.status != "completed":
        return {
            "job_id": job.id,
            "status": job.status,
            "message": "Labeling has not completed yet.",
        }

    return {
        "job_id": job.id,
        "status": job.status,
        "transactions": job.result,
    }

@router.post("/training/upload-labeled-csv")
async def upload_labeled_csv(
    file: UploadFile = File(...),
    db: Session = Depends(getfd),
) -> dict[str, int | str]:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()

    service = LabeledCsvUploadService(db)
    result = service.upload(content)

    return {
        "message": "Labeled CSV uploaded successfully",
        "inserted": result["inserted"],
    }