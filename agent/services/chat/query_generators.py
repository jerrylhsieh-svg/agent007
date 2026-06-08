from agent.services.chat.call_model import call_model


def generate_sql(message: str, schema: str) -> str:
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
{schema}

User question:
{message}
"""
    return call_model(prompt)

def identify_tables(message: str, tables: list[str]) -> str:
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
{tables}

User question:
{message}
"""
    return call_model(prompt)
