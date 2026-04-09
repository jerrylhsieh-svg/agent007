from dataclasses import dataclass

@dataclass
class TransactionRow:
    page_number: int
    date: str | None
    description: str
    amount: float | None
    balance: float | None
    raw_line: str