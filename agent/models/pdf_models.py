from dataclasses import dataclass

@dataclass
class TransactionRow:
    transaction_date: str | None
    posting_date: str | None
    description: str
    reference_number: int
    amount: float | None
    raw_line: str

@dataclass
class BankStatementRow:
    date: str | None
    description: str
    statement_type: str | None
    amount: float | None
    raw_line: str
