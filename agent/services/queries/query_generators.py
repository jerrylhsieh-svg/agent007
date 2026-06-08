from functools import cached_property

from sqlalchemy.orm import Session

from agent.services.chat.call_model import call_model
from agent.services.queries.get_tables_information import get_table_names, get_table_schema


class QueryGenerator():

    def __init__(self, message, db):
        self.message = message
        self.db = db

    @cached_property
    def table_list(self) -> list[str]:
        return get_table_names(self.db)
    
    @cached_property
    def table_name(self) -> str:
        name = self.identify_tables(self.message).strip().strip("`")
        if name not in self.table_list:
            raise ValueError(f"Invalid table selected by model: {name}")
        return name
    
    @cached_property
    def table_schema(self) -> list[dict]:
        return get_table_schema(self.db, self.table_name)

    def generate_sql(self) -> str:
        prompt = f"""
    You are a SQL generator for a personal finance app.

    Rules:
    - Return only SQL.
    - Use PostgreSQL syntax.
    - Only generate one SELECT statement.
    - Never use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, COPY, CALL, or EXEC.
    - Only use the tables and columns listed in the schema.
    - For spending amounts, use ABS(amount), because credit card charges may be stored as negative values.
    - Always add a LIMIT 50 unless the user asks for aggregation only.

    Schema:
    {self.table_schema}

    User question:
    {self.message}
    """
        return call_model(prompt)

    def identify_tables(self, message: str) -> str:
        prompt = f"""
    You are a table-selection assistant.

    Your job is to identify which database table the user is referring to.

    Rules:
    - Return exactly one table name.
    - Return only a table name, with no explanation.
    - The table name must be one of the allowed tables listed below.
    - Do not invent table names.
    - If the user question is ambiguous, choose the most likely table.
    - Do not generate SQL.

    Allowed tables:
    {self.table_list}

    User question:
    {message}
    """
        return call_model(prompt)

def handle_query_transactions(message: str, db: Session, **kwargs) -> str:
    generator = QueryGenerator(message=message, db=db)
    sql = generator.generate_sql()

    return sql