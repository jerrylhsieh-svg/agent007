from sqlalchemy import text
from sqlalchemy.orm import Session


query_session: dict[str, dict] = {}
    

def executing(message: str, db: Session, session_id: str, sql: str, **kwargs):
    state = query_session.get(session_id)
    if state is None:
        query_session[session_id] = {"step": "awaiting_approval"}
        return {
            "handled": True,
            "reply": f"Executing the following query:\n{sql}\nDo you approve? Please answer 'Yes' or 'No'"
        }
    
    step = state["step"]

    if step == "awaiting_approval":
        answer = message.strip()
        tried = state.get("file_type_retry", 0)
        if (not answer or answer not in ("Yes", "No")) and tried < 1:
            tried += 1
            return "Please give me a valid answer. 'Yes' or 'No'"
        elif answer == "Yes":
            result = db.execute(text(sql))
            rows = result.mappings().all()

            query_session.pop(session_id, None)

            return {
                "handled": True,
                "reply": rows,
            }
        else:
            query_session.pop(session_id, None)
            return "Did not receive an approval"
            

       