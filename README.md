# agent007

A local AI assistant built with **FastAPI** and **Ollama**, with a simple web UI, chat endpoint, PDF bank-statement extraction, and Google Sheets-backed transaction analysis.

## What it does

- Runs a local LLM through Ollama
- Serves a lightweight chat UI from FastAPI
- Supports a `/chat` API for normal assistant conversations
- Supports a simple multi-step file-writing flow in chat
- Accepts PDF uploads through `/pdf/extract`
- Extracts transaction and statement rows from supported bank / credit card PDFs
- Uploads parsed rows to Google Sheets
- Lets the chat assistant answer questions using transaction data stored in Google Sheets

## Current architecture

- **FastAPI** app for API + frontend
- **Ollama** container for local model inference
- **pdfplumber + PyMuPDF** for PDF parsing and scanned-PDF detection
- **gspread + Google service account credentials** for Google Sheets writes/reads
- **Docker Compose** for local development
