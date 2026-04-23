# agent007

A local AI assistant built with **FastAPI** and **Ollama**, with a simple web UI, chat endpoint, PDF bank-statement extraction, and Google Sheets-backed transaction analysis.

## What it does

- Runs a local LLM through Ollama
- Serves a lightweight web UI from FastAPI
- Supports a `/chat` API for assistant conversations
- Supports a simple multi-step file-writing flow in chat
- Accepts PDF uploads through `/pdf/extract`
- Extracts transaction and statement rows from supported bank and credit card PDFs
- Uploads parsed rows to Google Sheets
- Lets the assistant answer questions using transaction data stored in Google Sheets

## Current architecture

- **FastAPI** app for API and frontend
- **Ollama** for local model inference
- **pdfplumber + PyMuPDF** for PDF parsing and scanned-PDF detection
- **gspread + Google service account credentials** for Google Sheets reads and writes
- **Docker Compose** for local deployment

## Requirements

- Docker + Docker Compose
- Ollama-compatible model (default: `qwen2.5:1.5b`)
- Google service account JSON for Google Sheets access

## Environment

Create `agent/.env`:

```env
OLLAMA_HOST=http://ollama:11434
MODEL=qwen2.5:1.5b
GOOGLE_APPLICATION_CREDENTIALS_FILE=/run/secrets/gcp-service-account.json
```

## Local deployment

### 1. Clone the repo

```bash
git clone https://github.com/jerrylhsieh-svg/agent007.git
cd agent007
```

### 2. Mount Google credentials

Update the credentials volume in `docker-compose.yml` to point to your local JSON file:

```yaml
- /absolute/path/to/your-service-account.json:/run/secrets/gcp-service-account.json:ro
```

### 3. Start the app

```bash
docker compose up --build
```

### 4. Pull the model

In another terminal:

```bash
docker exec -it $(docker ps -qf "ancestor=ollama/ollama:latest") ollama pull qwen2.5:1.5b
```

### 5. Open the app

```text
http://localhost:8000
```

## Endpoints

- `GET /health`
- `POST /chat`
- `POST /pdf/extract`
