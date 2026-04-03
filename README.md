# agent007

A simple local AI agent built with FastAPI and Ollama.

This project provides:
- a small web UI served by FastAPI
- a `/chat` API endpoint for sending prompts
- a local Ollama container for running the model
- a lightweight Docker Compose setup for local development

## Project structure

```text
agent007/
├── docker-compose.yml
├── README.md
└── agent/
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py
    ├── services/
    │   └── call_model.py
    ├── static/
    │   ├── script.js
    │   └── style.css
    └── templates/
        └── index.html