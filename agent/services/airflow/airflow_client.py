from datetime import datetime, timezone
import os
import requests


class AirflowClient:

    def __init__(self):
        self.base_url = os.getenv(
            "AIRFLOW_URL",
            "http://airflow-apiserver:8080",
        )

        self.username = os.getenv("AIRFLOW_USERNAME")
        self.password = os.getenv("AIRFLOW_PASSWORD")

    def _get_token(self) -> str:
        response = requests.post(
            f"{self.base_url}/auth/token",
            json={
                "username": self.username,
                "password": self.password,
            },
            timeout=10,
        )

        response.raise_for_status()

        return response.json()["access_token"]

    def trigger_dag(
        self,
        dag_id: str,
        conf: dict | None = None,
    ) -> dict:

        token = self._get_token()

        response = requests.post(
            f"{self.base_url}/api/v2/dags/{dag_id}/dagRuns",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "logical_date": datetime.now(timezone.utc).isoformat(),
                "conf": conf or {},
            },
            timeout=10,
        )

        print(response.status_code)
        print(response.text)

        response.raise_for_status()

        return response.json()