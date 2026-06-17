from pydantic import BaseModel, Field
from typing import Literal


class Filter(BaseModel):
    field: str
    op: Literal["=", "!=", ">", ">=", "<", "<=", "contains"]
    value: str | int | float


class OrderBy(BaseModel):
    field: str 
    direction: Literal["asc", "desc"]


class Metric(BaseModel):
    function: Literal["sum", "avg", "count", "max", "min"]
    field: Literal["amount"] | None = None
    alias: Literal["total_amount", "avg_amount", "transaction_count", "max_amount", "min_amount"]


class QueryPlan(BaseModel):
    table: str

    select_fields: list[str] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)
    filters: list[Filter] = Field(default_factory=list)
    group_by: list[str] = Field(default_factory=list)
    order_by: list[OrderBy] = Field(default_factory=list)

    limit: int | None = 10