from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from agent.db.models.IdGenerator import generate_id
from agent.db.session import Base


class TransactionRecord(Base):
    __tablename__ = "transaction_records"

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=generate_id)
    date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    normalized_description: Mapped[str | None] = mapped_column(Text, nullable=True)
