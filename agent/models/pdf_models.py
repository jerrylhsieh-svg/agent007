from dataclasses import dataclass
from typing import Literal

@dataclass
class TransactionRow:
    transaction_date: str | None
    posting_date: str | None
    description: str
    reference_number: int
    amount: float | None

@dataclass
class BankStatementRow:
    date: str | None
    description: str
    statement_type: Literal["deposit", "withdraw"]
    amount: float | None

@dataclass
class BiltTransactionRow:
    date: str | None
    description: str
    amount: float | None
