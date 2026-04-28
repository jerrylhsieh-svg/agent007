from collections import defaultdict
from dataclasses import asdict

from agent.learning_models.labeler import Labeler
from agent.learning_models.constants import UNKNOWN_LABEL
from agent.models.labeling_job import UnlabeledRecord
from agent.repo.UnlabeledRecordRepository import UnlabeledRecordRepository
from agent.services.constants_and_dependencies import GSHEET_LABEL_GROUP_TAB, labeling_store
from agent.services.google_sheets import add_labels
import logging

logger = logging.getLogger(__name__)

def create_labeling_job(data):
    return labeling_store.create_job(len(data))

def run_transaction_labeling_job(job_id: str, transactions: list[dict], worksheet_name: str, merchant_label_service: Labeler) -> None:
    job = labeling_store.get_job(job_id)

    if job is None:
        raise ValueError("Labeling job not found")
    
    job.status = "running"
    labeling_store.update_job(job)

    labeled_results: list[dict] = []
    labeled, unlabeled = [], []
    for txn in transactions:
        prediction = asdict(merchant_label_service.predict_one(txn["description"]))

        labeled_txn = {
            **txn,
            "label": prediction["merchant_type"],
            "confidence": prediction["confidence"],
            "source": prediction["source"],
            "normalized_description": prediction["normalized_description"],
            "predicted_label": prediction["predicted_label"]
        }

        if prediction["merchant_type"] == UNKNOWN_LABEL:
            unlabeled.append(UnlabeledRecord(
                record_id=labeled_txn["id"], 
                sheet_name=worksheet_name, 
                description=labeled_txn["description"],
                normalized_description=labeled_txn["normalized_description"],
                predicted_label=labeled_txn["predicted_label"],
                confidence=labeled_txn["confidence"],
                priority_score=0.0,
                similar_count=1,
                total_amount_impact=labeled_txn["amount"],
                )
            )
        else:
            labeled.append((labeled_txn["id"], labeled_txn["label"]))

        labeled_results.append(labeled_txn)

        job.processed_records += 1
        job.result = labeled_results
        labeling_store.update_job(job)

    job.status = "completed"
    labeling_store.update_job(job)

    add_labels(worksheet_name, labeled)

    unlabel_repo = UnlabeledRecordRepository()
    all_unlabeled = unlabeled + unlabel_repo.get_records()
    unlabel_repo.insert_many(unlabeled)
    all_unlabeled = rerank(all_unlabeled)
    unlabel_repo.overwrite(all_unlabeled, GSHEET_LABEL_GROUP_TAB)

def rerank(records: list[UnlabeledRecord]) -> list[UnlabeledRecord]:
        grouped: dict[str, list[UnlabeledRecord]] = defaultdict(list)

        for record in records:
            grouped[record.normalized_description].append(record)

        consolidated: list[UnlabeledRecord] = []

        for normalized_description, group_records in grouped.items():
            representative = group_records[0]

            similar_count = sum(r.similar_count for r in group_records)
            total_amount = sum(abs(r.total_amount_impact or 0.0) for r in group_records)

            confidences = [
                r.confidence*r.similar_count
                for r in group_records
                if r.confidence is not None
            ]

            avg_confidence = (
                sum(confidences) / similar_count
                if confidences
                else 0.0
            )

            uncertainty_score = 1 - avg_confidence

            representative.normalized_description = normalized_description
            representative.similar_count = similar_count
            representative.total_amount_impact = total_amount
            representative.confidence = avg_confidence
            representative.priority_score = (
                similar_count * 10
                + min(total_amount, 500) * 0.1
                + uncertainty_score * 25
            )

            consolidated.append(representative)

        return sorted(
            consolidated,
            key=lambda r: r.priority_score,
            reverse=True,
        )