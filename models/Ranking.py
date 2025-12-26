from db import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    Text,
    UniqueConstraint,
    Float,
)
# =========================
# RANKING
# =========================
from datetime import datetime, timezone

class Ranking(Base):
    __tablename__ = "ranking"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    puzzle_id = Column(Integer, ForeignKey("puzzles.id"), nullable=True)

    # np. najlepszy czas
    best_time = Column(Float, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))