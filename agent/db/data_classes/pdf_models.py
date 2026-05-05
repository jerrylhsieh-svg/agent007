from dataclasses import dataclass, field
from typing import Literal
from uuid import uuid4

@dataclass
class FinancialRecordRow:
    date: str | None
    description: str
    amount: float
    id: str = field(default_factory=lambda: uuid4().hex[:12])
    label: str = ""

@dataclass(frozen=True)
class LineSchema:
    name: str
    columns: list[str]
    min_parts: int
    start_markers: list[str]
    end_markers: list[str]
    credit: bool = False
    statement_type_markers: dict[str, Literal['deposit', 'withdraw'] | None] | None = None