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
# DAILY PUZZLE
# =========================
class DailyPuzzle(Base):
    __tablename__ = "daily_puzzle"

    id = Column(Integer, primary_key=True)

    puzzle_id = Column(Integer, ForeignKey("puzzles.id"), nullable=False)
    date = Column(DateTime, nullable=False, unique=True)

    puzzle = relationship("Puzzle", back_populates="daily")
