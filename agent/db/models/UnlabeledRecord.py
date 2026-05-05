from datetime import datetime
from uuid import uuid4

from sqlalchemy import Date, DateTime, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from agent.db.session import Base


def generate_id() -> str:
    return uuid4().hex[:12]

class UnlabeledRecord(Base):
    __tablename__ = "unlabeled_records"

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=generate_id)
    source_record_id: Mapped[str] = mapped_column(String(12), nullable=False)
    record_type: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    predicted_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("source_record_id", "record_type", name="uq_unlabeled_source_record"),
    )