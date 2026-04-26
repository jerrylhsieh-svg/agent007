# agent/api/labeling_routes.py

from fastapi import APIRouter, HTTPException

from agent.services.constants_and_dependencies import labeling_store


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