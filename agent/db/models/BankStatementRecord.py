from uuid import uuid4

from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from agent.db.session import Base



class BankStatementRecord(Base):
    __tablename__ = "bank_statement_records"

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=uuid4().hex[:12])
    date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    normalized_description: Mapped[str | None] = mapped_column(Text, nullable=True)
