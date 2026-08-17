from fastapi import APIRouter

from agent.services.airflow.airflow_client import AirflowClient

router = APIRouter(prefix="/training")

airflow = AirflowClient()


@router.post("/retrain")
def retrain_models():
    dag_run = airflow.trigger_dag(
        dag_id="model_retraining",
        conf={
            "models": ["transaction", "statement"]
        },
    )

    return {
        "ok": True,
        "dag_run_id": dag_run["dag_run_id"],
        "state": dag_run["state"],
    }