from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from agent.db.models.IdGenerator import generate_id
from agent.db.session import Base


class UnlabeledRecordGroup(Base):
    __abstract__ = True

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=generate_id)
    date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    predicted_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    similar_count: Mapped[int | None] = mapped_column(Integer, default=1)
    total_amount_impact: Mapped[float | None] = mapped_column(Float, nullable=True)
