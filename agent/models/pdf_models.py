from dataclasses import dataclass

@dataclass
class TransactionRow:
    transaction_date: str | None
    posting_date: str | None
    description: str
    reference_number: int
    amount: float | None
    raw_line: str