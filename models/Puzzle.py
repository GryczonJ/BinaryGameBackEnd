from enum import Enum
from .PuzzleType import PuzzleType
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
# PUZZLES
# =========================
class Puzzle(Base):
    __tablename__ = "puzzles"

    id = Column(Integer, primary_key=True, index=True)

    grid_size = Column(Integer, nullable=False)

    # zapis planszy w formacie JSON lub tekstowym
    puzzle_data = Column(Text, nullable=False)

    # poprawne rozwiązanie
    solution = Column(Text, nullable=False)

    type = Column(SAEnum(PuzzleType), default=PuzzleType.STORY)
    difficulty = Column(Integer, nullable=True)

    # czy może być używana jako daily template
    is_daily_template = Column(Boolean, default=False)

    daily = relationship("DailyPuzzle", back_populates="puzzle")
    solutions = relationship("Solution", back_populates="puzzle")


