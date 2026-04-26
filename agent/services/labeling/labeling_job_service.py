from agent.services.constants_and_dependencies import labeling_store
from agent.services.labeling.merchant_label_service import MerchantLabelService


merchant_label_service = MerchantLabelService()


def run_labeling_job(job_id: str, transactions: list[dict]) -> None:
    job = labeling_store.get_job(job_id)

    if job is None:
        return

    try:
        job.status = "running"
        labeling_store.update_job(job)

        labeled_results: list[dict] = []

        for txn in transactions:
            prediction = merchant_label_service.label_one(txn["description"])

            labeled_txn = {
                **txn,
                "label": prediction.merchant_type,
                "confidence": prediction.confidence,
                "source": prediction.source,
            }

            labeled_results.append(labeled_txn)

            job.processed_records += 1
            job.result = labeled_results
            labeling_store.update_job(job)

        job.status = "completed"
        labeling_store.update_job(job)

    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        labeling_store.update_job(job)