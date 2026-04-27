from collections import defaultdict
from dataclasses import asdict

from agent.ml.merchant_predictor import UNKNOWN_LABEL
from agent.models.labeling_job import UnlabeledRecord
from agent.services.constants_and_dependencies import GSHEET_LABEL_TAB, GSHEET_NAME, LABEL_HEADERS, labeling_store
from agent.services.google_sheets import add_labels, append_data, build_gsheet_rows
from agent.services.labeling.merchant_label_service import MerchantLabelService


merchant_label_service = MerchantLabelService()

def create_labeling_job(data):
    return labeling_store.create_job(len(data))

def run_labeling_job(job_id: str, transactions: list[dict], worksheet_name) -> None:
    job = labeling_store.get_job(job_id)

    if job is None:
        return

    try:
        job.status = "running"
        labeling_store.update_job(job)

        labeled_results: list[dict] = []
        labeled, unlabeled = [], []
        for txn in transactions:
            prediction = merchant_label_service.label_one(txn["description"])

            labeled_txn = {
                **txn,
                "label": prediction["merchant_type"],
                "confidence": prediction["confidence"],
                "source": prediction["source"],
            }

            if prediction["merchant_type"] == UNKNOWN_LABEL:
                unlabeled.append(UnlabeledRecord(
                    record_id=labeled_txn["id"], 
                    sheet_name=worksheet_name, 
                    description=labeled_txn["description"],
                    normalized_description=(labeled_txn["normalized_description"]),
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
        rows = build_gsheet_rows(
            data=[asdict(row) for row in unlabeled],
            fields=LABEL_HEADERS,
        )
        append_data(
            spreadsheet_name=GSHEET_NAME,
            worksheet_name=GSHEET_LABEL_TAB,
            rows=rows,
            headers=LABEL_HEADERS
        )

    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        labeling_store.update_job(job)

def rerank(records: list[UnlabeledRecord]) -> list[UnlabeledRecord]:
        pending = [r for r in records]

        grouped: dict[str, list[UnlabeledRecord]] = defaultdict(list)

        for record in pending:
            key = record.normalized_description
            grouped[key].append(record)

        for group_records in grouped.values():
            similar_count = len(group_records)
            total_amount = sum(abs(r.total_amount_impact or 0.0) for r in group_records)

            for record in group_records:
                confidence = record.confidence if record.confidence is not None else 0.0
                uncertainty_score = 1 - confidence

                record.similar_count = similar_count
                record.total_amount_impact = total_amount
                record.priority_score = (
                    similar_count * 10
                    + min(total_amount, 500) * 0.1
                    + uncertainty_score * 25
                )

        return sorted(
            records,
            key=lambda r: r.priority_score,
            reverse=True,
        )