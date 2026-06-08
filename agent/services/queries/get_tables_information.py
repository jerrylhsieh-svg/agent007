from sqlalchemy import text
from sqlalchemy.orm import Session

PUBLIC_SCHEMA = "public"

def get_table_names(db: Session, table_schema: str = PUBLIC_SCHEMA) -> list[str]:
    query = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = :table_schema
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)

    result = db.execute(query, {"table_schema": table_schema})

    return [row.table_name for row in result]


def get_table_schema(db: Session, table_name: str, table_schema: str = PUBLIC_SCHEMA) -> list[dict]:
    query = text("""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = :table_schema
          AND table_name = :table_name
        ORDER BY ordinal_position;
    """)

    result = db.execute(
        query,
        {
            "table_schema": table_schema,
            "table_name": table_name,
        },
    )

    return [dict(row._mapping) for row in result]