from sqlalchemy import Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from agent.db.models.IdGenerator import generate_id
from agent.db.session import Base


class UnlabeledBaseRecord(Base):
    __abstract__ = True

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=generate_id)
    record_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    predicted_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("id", "record_type", name="uq_unlabeled_source_record"),
    )