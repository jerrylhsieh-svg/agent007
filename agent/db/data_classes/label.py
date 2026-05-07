from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Literal
from uuid import uuid4


JobStatus = Literal["pending", "running", "completed", "failed"]


@dataclass
class LabelingJob:
    id: str
    status: JobStatus = "pending"
    total_records: int = 0
    processed_records: int = 0
    error_message: str | None = None
    result: list[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class UnlabeledRecord:
    id: str
    description: str 
    normalized_description: str
    predicted_label: str
    confidence: float
    priority_score: float
    similar_count: int
    total_amount_impact: float
    record_type: str

@dataclass(frozen=True)
class LabelSuggested:
    suggested_label: str
    confidence: float
    reason: str

@dataclass
class TrainRecord:
    description: str 
    label: str
    statement_type: str = ""
    id: int | None = None

class InMemoryLabelingStore:
    def __init__(self) -> None:
        self._jobs: dict[str, LabelingJob] = {}
        self._lock = Lock()

    def create_job(self, total_records: int) -> LabelingJob:
        job = LabelingJob(
            id=str(uuid4()),
            total_records=total_records,
        )

        with self._lock:
            self._jobs[job.id] = job

        return job

    def get_job(self, job_id: str) -> LabelingJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update_job(self, job: LabelingJob) -> None:
        with self._lock:
            self._jobs[job.id] = job