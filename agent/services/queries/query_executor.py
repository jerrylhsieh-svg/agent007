from functools import cached_property

from sqlalchemy import text

from agent.services.queries.query_generators import generating_query


class QueryExecutor():

    query_session: dict[str, dict] = {}

    def __init__(self, message, db, session_id):
        self.message = message
        self.db = db
        self.session_id = session_id

    @cached_property
    def sql(self) -> list[str]:
        return generating_query(self.message, self.db)

    def executing(self, **kwargs):
        state = self.query_session.get(self.session_id)
        if state is None:
            self.query_session[self.session_id] = {"step": "awaiting_approval"}
            return {
                "handled": True,
                "reply": f"Executing the following query:\n{self.sql}\nDo you approve? Please answer 'Yes' or 'No'"
            }
        
        step = state["step"]

        if step == "awaiting_approval":
            answer = self.message.strip()
            tried = state.get("file_type_retry", 0)
            if (not answer or answer not in ("Yes", "No")) and tried < 1:
                tried += 1
                return "Please give me a valid answer. 'Yes' or 'No'"
            elif answer == "Yes":
                result = self.db.execute(text(self.sql))
                rows = result.mappings().all()

                self.query_session.pop(self.session_id, None)

                return {
                    "handled": True,
                    "reply": rows,
                }
            else:
                self.query_session.pop(self.session_id, None)
                return "Did not receive an approval"
                

        