from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from agent.db.models.IdGenerator import generate_id
from agent.db.session import Base


class UnlabeledRecordGroup(Base):
    __abstract__ = True

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=generate_id)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_description: Mapped[str] = mapped_column(Text, nullable=False)
    predicted_label: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False)
    similar_count: Mapped[int] = mapped_column(Integer, default=1)
    total_amount_impact: Mapped[float] = mapped_column(Float, nullable=False)
