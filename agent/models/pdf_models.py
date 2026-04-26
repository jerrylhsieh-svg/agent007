from dataclasses import dataclass
from typing import Literal

@dataclass
class TransactionRow:
    date: str | None
    description: str
    amount: float | None

@dataclass
class BankStatementRow:
    date: str | None
    description: str
    statement_type: Literal["deposit", "withdraw"]
    amount: float | None
