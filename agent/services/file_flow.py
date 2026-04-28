from agent.services.save_file import save_text_file

# session_id -> state
file_sessions: dict[str, dict] = {}


SAVE_TRIGGERS = {
    "help me write a file",
    "write a file",
    "create a file",
    "save a file",
    "make a file",
}

IS_TRANSACTION_TRIGGERS = [
    "credit card spending summary",
]

IS_STATEMENT_TRIGGERS = [
    "bank statement summary",
]

IS_WITHDRAW_TRIGGERS = [
    "bank withdraw summary",
]


def normalize(text: str) -> str:
    return text.strip().lower()


def should_start_file_flow(message: str) -> bool:
    msg = normalize(message)
    return any(trigger in msg for trigger in SAVE_TRIGGERS)


def should_start_transaction_flow(message: str) -> bool:
    msg = normalize(message)
    return any(trigger in msg for trigger in IS_TRANSACTION_TRIGGERS)

def should_start_statement_flow(message: str) -> bool:
    msg = normalize(message)
    return any(trigger in msg for trigger in IS_STATEMENT_TRIGGERS)

def should_start_withdraw_flow(message: str) -> bool:
    msg = normalize(message)
    return any(trigger in msg for trigger in IS_WITHDRAW_TRIGGERS)


def handle_file_flow(session_id: str, message: str):
    state = file_sessions.get(session_id)

    if state is None:
        if should_start_file_flow(message):
            file_sessions[session_id] = {"step": "awaiting_filename"}
            return {
                "handled": True,
                "reply": "What should the file be named?"
            }

        return {"handled": False}

    step = state["step"]

    if step == "awaiting_filename":
        filename = message.strip()
        if not filename:
            return {
                "handled": True,
                "reply": "Please give me a valid file name."
            }

        file_sessions[session_id] = {
            "step": "awaiting_content",
            "filename": filename,
        }
        return {
            "handled": True,
            "reply": f"What would you like to write in `{filename}`?"
        }

    if step == "awaiting_content":
        filename = state["filename"]
        content = message

        try:
            path = save_text_file(filename, content)
        except Exception as e:
            file_sessions.pop(session_id, None)
            return {
                "handled": True,
                "reply": f"I couldn't save the file: {e}"
            }

        file_sessions.pop(session_id, None)
        return {
            "handled": True,
            "reply": f"Saved `{filename}` to `{path}`."
        }

    file_sessions.pop(session_id, None)
    return {"handled": False}