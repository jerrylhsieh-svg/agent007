from agent.ml.merchant_predictor import UNKNOWN_LABEL
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
                unlabeled.append({"id":txn["id"], "description":txn["description"], "sheet_name":worksheet_name})
            else:
                labeled.append((txn["id"], prediction["merchant_type"]))

            labeled_results.append(labeled_txn)

            job.processed_records += 1
            job.result = labeled_results
            labeling_store.update_job(job)

        job.status = "completed"
        labeling_store.update_job(job)

        add_labels(worksheet_name, labeled)
        rows = build_gsheet_rows(
            data=unlabeled,
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