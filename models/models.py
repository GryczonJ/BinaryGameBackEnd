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

Base = declarative_base()

# =========================
# OPTIONAL – HINT LOGS
# =========================
class HintLog(Base):
    __tablename__ = "hint_logs"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    puzzle_id = Column(Integer, ForeignKey("puzzles.id"), nullable=False)

    hint_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
