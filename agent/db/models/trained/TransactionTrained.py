from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from agent.db.session import Base



class TransactionTrained(Base):
    __tablename__ = "transaction_trained"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    description: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False, default="")
