from collections import defaultdict
from dataclasses import asdict


from agent.db.data_classes.pdf_models import FinancialRecordRow
from agent.db.session import SessionLocal
from agent.learning_models.labeler import Labeler
from agent.learning_models.constants import UNKNOWN_LABEL
from agent.db.data_classes.label import UnlabeledRecord
from agent.repo.financial_record_repository import FinancialRecordRepository
from agent.repo.unlabeled_geoup_repository import UnlabeledGroupRepository
from agent.repo.unlabeled_record_repository import UnlabeledRecordRepository
from agent.services.constants_and_dependencies import labeling_store
import logging

logger = logging.getLogger(__name__)

def create_labeling_job(data):
    return labeling_store.create_job(len(data))

def run_transaction_labeling_job(
        job_id: str, 
        transactions: list[FinancialRecordRow], 
        merchant_label_service: Labeler, 
    ) -> None:
    db = SessionLocal()
    job = labeling_store.get_job(job_id)

    if job is None:
        raise ValueError("Labeling job not found")
    
    job.status = "running"
    labeling_store.update_job(job)
    repo = FinancialRecordRepository(db, merchant_label_service.file_type)

    labeled_results: list[dict] = []
    unlabeled = []
    for transaction in transactions:
        prediction = asdict(merchant_label_service.predict_one(transaction.description))

        if prediction["merchant_type"] == UNKNOWN_LABEL:
            unlabeled.append(UnlabeledRecord(
                id=transaction.id, 
                description=transaction.description,
                normalized_description=prediction["normalized_description"],
                predicted_label=prediction["predicted_label"],
                confidence=prediction["confidence"],
                priority_score=0.0,
                similar_count=1,
                total_amount_impact=transaction.amount,
                record_type=merchant_label_service.file_type,
                )
            )
        else:
            transaction.label = prediction["merchant_type"]
            repo.update_record(transaction)

        labeled_results.append(asdict(transaction))

        job.processed_records += 1
        job.result = labeled_results
        labeling_store.update_job(job)

    job.status = "completed"
    labeling_store.update_job(job)

    unlabel_repo = UnlabeledRecordRepository(db, merchant_label_service.file_type)
    all_unlabeled = unlabeled +  unlabel_repo.get_records()
    unlabel_repo.insert_many(unlabeled)
    unlabel_group_repo = UnlabeledGroupRepository(db, merchant_label_service.file_type)
    all_unlabeled = rerank(all_unlabeled)
    unlabel_group_repo.upsert_many(all_unlabeled)

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