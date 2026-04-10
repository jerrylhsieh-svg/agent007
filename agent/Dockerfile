FROM python:3.12-slim

WORKDIR /app

COPY . /app

COPY requirements.txt .
RUN pip install -r requirements.txt

CMD ["uvicorn", "agent.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app"]