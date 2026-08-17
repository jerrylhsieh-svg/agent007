from datetime import datetime

from airflow.sdk import dag, task
from agent.db.session import SessionLocal
from agent.learning_models.train_merchant_model import train


@dag(
    dag_id="model_retraining",
    schedule=None,
    catchup=False,
    tags=["ml", "training"],
)
def model_retraining():

    @task
    def train_transaction():
        db = SessionLocal()

        try:
            return train("transaction", db)
        except Exception as e:
            print(f"Train failed due to {e}")
        finally:
            db.close()

    @task
    def train_statement():
        db = SessionLocal()

        try:
            return train("statement", db)
        except Exception as e:
            print(f"Train failed due to {e}")
        finally:
            db.close()

    train_transaction()
    train_statement()


model_retraining()