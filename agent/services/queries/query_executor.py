from sqlalchemy.orm import Session

from agent.services.queries.query_generators import generating_query


class QueryExecutor():

    query_session: dict[str, dict] = {}

    def __init__(self, message, db, query, session_id):
        self.message = message
        self.db = db
        self.query = query
        self.state = self.query_session.get(session_id)
        self.retry = 0
    

def executing(message: str, db: Session, session_id: str, **kwargs):
    sql = generating_query(message, db)
    executor = QueryExecutor(message, db, sql, session_id)
    if executor.state is None:
        executor.query_session[session_id] = {"step": "awaiting_approval"}
        return {
            "handled": True,
            "reply": f"Executing the following query:\n{executor.query}\nDo you approve? Please answer 'Yes' or 'No'"
        }
    
    step = executor.query_session[session_id]["step"]

    if step == "awaiting_approval":
        answer = message.strip()
        if (not answer or answer not in ("Yes", "No")) and executor.retry < 1:
            executor.retry += 1
            return "Please give me a valid answer. 'Yes' or 'No'"
        elif answer == "Yes":
            pass
        else:
            executor.query_session.pop(session_id, None)
            return "Did not receive an approval"
            

       