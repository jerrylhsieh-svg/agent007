from dataclasses import dataclass, field
from typing import Literal
from uuid import uuid4

@dataclass
class TransactionRow:
    date: str | None
    description: str
    amount: float | None
    id: str = field(default_factory=lambda: uuid4().hex[:12])
    label: str = ""

@dataclass
class BankStatementRow:
    date: str | None
    description: str
    statement_type: Literal["deposit", "withdraw"]
    amount: float | None
    id: str = field(default_factory=lambda: uuid4().hex[:12])
    label: str = ""
