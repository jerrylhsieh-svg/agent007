from agent.services.chat.call_model import call_model


def generate_sql_from_question(message: str, schema: str) -> str:
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
