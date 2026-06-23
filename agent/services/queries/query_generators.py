from functools import cached_property
import json
from typing import Any

from sqlalchemy.orm import Session

from agent.db.models.query_generator.query_plan import Filter, Metric, OrderBy, QueryPlan
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

    def generate_query_plan(self, retry_msg="") -> dict:
        prompt = f"""
You are a query planner for a personal finance app.

Return only valid JSON. Do not return SQL.

The JSON must match this shape:

{{
  "table": "transaction_records",
  "select_fields": ["date", "amount"],
  "metrics": [],
  "filters": [
    {{"field": "category", "op": "=", "value": "Food"}}
  ],
  "group_by": [],
  "order_by": [
    {{"field": "amount", "direction": "desc"}}
  ],
  "limit": 50
}}

{retry_msg if retry_msg else ""}

Allowed table:
{self.table_name}

Allowed fields:
{[c['column_name'] for c in self.table_schema]}

Rules:
- Use "amount" for transaction amount.
- For spending summaries, use metric function "sum" with field "amount" and alias "total_amount".
- If the user asks for largest spending, order by "amount" desc.
- If the user asks for spending by category, group_by should include "category" and metrics should include SUM(amount).
- Use limit 50 unless the user asks for aggregation only.
- If the request cannot be answered with the allowed fields, return:
  {{"table": "transactions", "select_fields": [], "metrics": [], "filters": [], "group_by": [], "order_by": [], "limit": 50}}

User question:
{self.message}
"""

        return json.loads(call_model(prompt))


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
    
    def validate_plan_against_schema(self, plan: dict) -> QueryPlan:

        columns = set(c['column_name'] for c in self.table_schema)
        existing_plan = QueryPlan(table=plan["table"])

        for field in plan["select_fields"]:
            if field not in columns:
                raise ValueError(f"Column not in the table: {field}.\n Columns include in the table {self.table_name} are {self.table_schema}")
        existing_plan.select_fields = plan["select_fields"]

        for filter in plan["filters"]:
            if filter['field'] not in columns:
                raise ValueError(f"Column not in the table: {filter['field']}")
            existing_plan.filters.append(Filter(field=filter['field'], op=filter['op'], value=filter['value']))

        for group_by in plan["group_by"]:
            if group_by not in columns:
                raise ValueError(f"Column not in the table: {group_by}")
        existing_plan.group_by = plan["group_by"]


        for metric in plan["metrics"]:
            if metric["field"] is not None and metric.field not in columns:
                raise ValueError(f"Column not in the table: {metric['field']}")
            existing_plan.metrics.append(Metric(function=metric['function'], field=metric['field'], alias=metric['alias']))

        if existing_plan.metrics is None and existing_plan.select_fields is None:
            raise ValueError("No column been selected")

        allowed_order_fields = columns | {metric.alias for metric in plan["metrics"]}

        for order in plan["order_by"]:
            if order["field"] not in allowed_order_fields:
                raise ValueError(f"Column not allowed in ORDER BY: {order['field']}")
            existing_plan.order_by.append(OrderBy(field=order["field"], direction=order["direction"]))

        if plan["limit"] is not None and (plan["limit"] < 1 or plan["limit"] > 50):
            raise ValueError(f"Invalid limit: {plan['limit']}")
        existing_plan.limit = plan["limit"]

        return existing_plan
    
    def build_sql(self, plan: QueryPlan) -> str:

        select_parts = []

        for field in plan.select_fields:
            select_parts.append(field)

        for metric in plan.metrics:
            if metric.function == "count":
                select_parts.append(f"COUNT(*) AS {metric.alias}")
            elif metric.field == "amount":
                select_parts.append(
                    f"{metric.function.upper()}(ABS(amount)) AS {metric.alias}"
                )
            else:
                raise ValueError(f"Unsupported metric: {metric}")

        sql_parts = [
            f"SELECT {', '.join(select_parts)}",
            f"FROM {plan.table}",
        ]

        where_parts = []

        for i, filter_ in enumerate(plan.filters):
            param_name = f"p{i}"

            if filter_.op == "contains":
                where_parts.append(f"{filter_.field} ILIKE :{param_name}")
            else:
                where_parts.append(f"{filter_.field} {filter_.op} :{param_name}")

        if where_parts:
            sql_parts.append("WHERE " + " AND ".join(where_parts))

        if plan.group_by:
            sql_parts.append("GROUP BY " + ", ".join(plan.group_by))

        if plan.order_by:
            order_parts = [
                f"{item.field} {item.direction.upper()}"
                for item in plan.order_by
            ]
            sql_parts.append("ORDER BY " + ", ".join(order_parts))

        if plan.limit is not None and not plan.metrics:
            sql_parts.append(f"LIMIT {plan.limit}")

        return " ".join(sql_parts)

def handle_query_transactions(message: str, db: Session, **kwargs) -> str:
    generator = QueryGenerator(message=message, db=db)

    max_attempts = 2
    last_error = ""

    for _ in range(max_attempts):
        try:
            query_detail = generator.generate_query_plan(
                retry_msg=str(last_error) if last_error else ""
            )

            plan = generator.validate_plan_against_schema(query_detail)
            sql = generator.build_sql(plan)

            return sql

        except ValueError as e:
            last_error = e

        except Exception:
            raise

    raise ValueError(
        f"Failed to generate a valid query plan after {max_attempts} attempts. "
        f"Last error: {last_error}"
    )