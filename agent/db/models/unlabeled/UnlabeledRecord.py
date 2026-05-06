from sqlalchemy import Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from agent.db.models.IdGenerator import generate_id
from agent.db.session import Base


class UnlabeledBaseRecord(Base):
    __abstract__ = True

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=generate_id)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)

    predicted_label: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False)