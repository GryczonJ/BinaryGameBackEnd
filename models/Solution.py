from datetime import datetime
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
from sqlalchemy.orm import relationship, declarative_base
# =========================
# SOLUTIONS
# =========================
class Solution(Base):
    __tablename__ = "solutions"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    puzzle_id = Column(Integer, ForeignKey("puzzles.id"), nullable=False)

    # czas rozwiązania w sekundach
    time = Column(Float, nullable=True)

    is_correct = Column(Boolean, default=False)

    # jak użytkownik rozwiązał — zapis planszy
    submission_grid = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="solutions")
    puzzle = relationship("Puzzle", back_populates="solutions")

    __table_args__ = (
        UniqueConstraint("user_id", "puzzle_id", name="unique_user_puzzle_solution"),
    )