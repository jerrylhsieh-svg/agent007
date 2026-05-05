from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from agent.db.models.unlabeled import UnlabeledStatementRecord
from agent.db.models.unlabeled.UnlabeledTransactionRecord import UnlabeledTransactionRecord
import agent.services.labeling.labeling_job_service as service
from agent.learning_models.constants import UNKNOWN_LABEL
from agent.db.data_classes.label import UnlabeledRecord


@dataclass
class FakePrediction:
    merchant_type: str
    confidence: float
    source: str
    normalized_description: str
    predicted_label: str


class FakeLabeler:
    def __init__(self, predictions):
        self.predictions = iter(predictions)

    def predict_one(self, description: str):
        return next(self.predictions)

    def get_worksheet(self):
        return "transactions"

    def get_label_sheet(self):
        return "unlabeled_raw"

    def get_label_group_sheet(self):
        return "unlabeled_grouped"

    def get_label_header(self):
        return [
            "id",
            "description",
            "normalized_description",
            "predicted_label",
            "confidence",
            "priority_score",
            "similar_count",
            "total_amount_impact",
        ]


class FakeLabelingStore:
    def __init__(self, job=None):
        self.job = job
        self.updated_jobs = []

    def create_job(self, total_records):
        return SimpleNamespace(
            id="job-123",
            total_records=total_records,
            processed_records=0,
            status="pending",
            result=[],
        )

    def get_job(self, job_id):
        return self.job

    def update_job(self, job):
        self.updated_jobs.append(
            SimpleNamespace(
                status=job.status,
                processed_records=job.processed_records,
                result=list(job.result) if getattr(job, "result", None) else [],
            )
        )


def make_unlabeled(
    *,
    id: str,
    normalized_description: str,
    confidence: float,
    similar_count: int,
    total_amount_impact: float,
):
    return UnlabeledRecord(
        id=id,
        description=normalized_description,
        normalized_description=normalized_description,
        predicted_label=UNKNOWN_LABEL,
        confidence=confidence,
        priority_score=0.0,
        similar_count=similar_count,
        total_amount_impact=total_amount_impact,
    )


def test_create_labeling_job_uses_data_length(monkeypatch):
    fake_store = FakeLabelingStore()
    monkeypatch.setattr(service, "labeling_store", fake_store)

    job = service.create_labeling_job([{"id": "1"}, {"id": "2"}])

    assert job.total_records == 2
    assert job.status == "pending"


def test_rerank_groups_by_normalized_description_and_sorts_by_priority():
    records = [
        make_unlabeled(
            id="1",
            normalized_description="uber trip",
            confidence=0.2,
            similar_count=1,
            total_amount_impact=-20.0,
        ),
        make_unlabeled(
            id="2",
            normalized_description="uber trip",
            confidence=0.8,
            similar_count=2,
            total_amount_impact=30.0,
        ),
        make_unlabeled(
            id="3",
            normalized_description="unknown store",
            confidence=0.1,
            similar_count=1,
            total_amount_impact=10.0,
        ),
    ]

    result = service.rerank(records)

    assert len(result) == 2

    uber = next(r for r in result if r.normalized_description == "uber trip")
    assert uber.similar_count == 3
    assert uber.total_amount_impact == 50.0
    assert uber.confidence == pytest.approx(0.6)

    expected_priority = 3 * 10 + 50.0 * 0.1 + (1 - 0.6) * 25
    assert uber.priority_score == pytest.approx(expected_priority)

    assert result[0].priority_score >= result[1].priority_score


def test_rerank_handles_none_amount_and_missing_confidence():
    records = [
        make_unlabeled(
            id="1",
            normalized_description="mystery merchant",
            confidence=None,
            similar_count=1,
            total_amount_impact=None,
        ),
    ]

    result = service.rerank(records)

    assert len(result) == 1
    assert result[0].confidence == 0.0
    assert result[0].total_amount_impact == 0.0
    assert result[0].priority_score == pytest.approx(35.0)


def test_run_transaction_labeling_job_raises_when_job_not_found(monkeypatch):
    fake_store = FakeLabelingStore(job=None)
    monkeypatch.setattr(service, "labeling_store", fake_store)

    labeler = FakeLabeler([])

    with pytest.raises(ValueError, match="Labeling job not found"):
        service.run_transaction_labeling_job(
            job_id="missing-job",
            transactions=[],
            merchant_label_service=labeler,
        )


def test_run_transaction_labeling_job_labels_known_and_stores_unknown(monkeypatch):
    job = SimpleNamespace(
        id="job-123",
        status="pending",
        processed_records=0,
        result=[],
    )
    fake_store = FakeLabelingStore(job=job)
    monkeypatch.setattr(service, "labeling_store", fake_store)

    add_labels_mock = Mock()
    monkeypatch.setattr(service, "add_labels", add_labels_mock)

    created_repos = {}

    class FakeUnlabeledRecordRepository:
        def __init__(self, db, record_type):
            self.db = db
            self.record_type = record_type
            self.record_class = (
                UnlabeledStatementRecord
                if record_type == "statement"
                else UnlabeledTransactionRecord
            )
            self.inserted_records = None
            self.overwritten_records = None

        def get_records(self):
            return [
                make_unlabeled(
                    id="existing-1",
                    normalized_description="existing unknown",
                    confidence=0.4,
                    similar_count=1,
                    total_amount_impact=25.0,
                )
            ]

        def insert_many(self, records, fields):
            self.inserted_records = records
            self.insert_fields = fields

        def overwrite(self, records, fields):
            self.overwritten_records = records
            self.overwrite_fields = fields

    monkeypatch.setattr(
        service,
        "UnlabeledRecordRepository",
        FakeUnlabeledRecordRepository,
    )

    transactions = [
        {
            "id": "txn-1",
            "description": "Whole Foods",
            "amount": 12.5,
        },
        {
            "id": "txn-2",
            "description": "Mystery Store",
            "amount": -40.0,
        },
    ]

    labeler = FakeLabeler(
        [
            FakePrediction(
                merchant_type="Merchandise",
                confidence=0.95,
                source="model",
                normalized_description="whole foods",
                predicted_label="Merchandise",
            ),
            FakePrediction(
                merchant_type=UNKNOWN_LABEL,
                confidence=0.2,
                source="model",
                normalized_description="mystery store",
                predicted_label=UNKNOWN_LABEL,
            ),
        ]
    )

    service.run_transaction_labeling_job(
        job_id="job-123",
        transactions=transactions,
        merchant_label_service=labeler,
    )

    assert job.status == "completed"
    assert job.processed_records == 2
    assert len(job.result) == 2

    assert job.result[0]["label"] == "Merchandise"
    assert job.result[0]["confidence"] == 0.95

    assert job.result[1]["label"] == UNKNOWN_LABEL
    assert job.result[1]["normalized_description"] == "mystery store"

    add_labels_mock.assert_called_once_with(
        "transactions",
        [("txn-1", "Merchandise")],
    )

    statuses = [updated.status for updated in fake_store.updated_jobs]
    assert statuses[0] == "running"
    assert statuses[-1] == "completed"