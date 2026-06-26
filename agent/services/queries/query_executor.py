from sqlalchemy import text

from agent.services.queries.query_generators import generating_query


class QueryExecutor():

    query_session: dict[str, dict] = {}

    def executing(self, message, db, session_id, history, **kwargs):
        state = self.query_session.get(session_id)
        if state is None:
            sql = generating_query(message, db, history)
            self.query_session[session_id] = {"step": "awaiting_approval", "sql": sql, "retry": 0,}
            return f"Executing the following query:\n{sql}\nDo you approve? Please answer 'Yes' or 'No'"
        
        step = state["step"]

        if step == "awaiting_approval":
            answer = message.strip()
            tried = state.get("retry", 0)
            if (not answer or answer not in ("Yes", "No")) and tried < 1:
                state["retry"] += 1
                return "Please give me a valid answer. 'Yes' or 'No'"
            elif answer == "Yes":
                try:
                    result = db.execute(text(state['sql']))
                    rows = result.mappings().all()

                    self.query_session.pop(session_id, None)

                    return f"Query result: {rows}"
                except Exception as e:
                    self.query_session.pop(session_id, None)
                    return f"Query failed due to {e}"
            else:
                self.query_session.pop(session_id, None)
                return "Did not receive an approval"
                

query_executor = QueryExecutor()       