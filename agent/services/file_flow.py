from agent.services.save_file import save_text_file

file_sessions: dict[str, dict] = {}


def handle_file_flow(session_id: str, message: str):
    state = file_sessions.get(session_id)

    if state is None:
        file_sessions[session_id] = {"step": "awaiting_filename"}
        return {
            "handled": True,
            "reply": "What should the file be named?"
        }

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