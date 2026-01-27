import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean, ForeignKey, Date
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship
from db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))

    login = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    nick = Column(String(100))
    avatar = Column(Text)  # Supports base64 images

    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    solves = relationship("Solve", back_populates="user", cascade="all, delete-orphan")
    ai_hints = relationship("AiHint", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UNIQUEIDENTIFIER, ForeignKey("users.id"), nullable=False)

    token = Column(String(255), unique=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="sessions")


class Puzzle(Base):
    __tablename__ = "puzzles"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))

    type = Column(String(20), nullable=False)  # story | daily | random
    difficulty = Column(Integer, nullable=False)
    size = Column(Integer, nullable=False)

    grid_solution = Column(Text, nullable=False)
    grid_initial = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    solves = relationship("Solve", back_populates="puzzle", cascade="all, delete-orphan")
    daily_entry = relationship("DailyPuzzle", back_populates="puzzle", uselist=False)
    story_entry = relationship("StoryPuzzle", back_populates="puzzle", uselist=False)
    ai_hints = relationship("AiHint", back_populates="puzzle", cascade="all, delete-orphan")


class StoryPuzzle(Base):
    __tablename__ = "story_puzzles"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    puzzle_id = Column(UNIQUEIDENTIFIER, ForeignKey("puzzles.id"), nullable=False)

    order_index = Column(Integer, nullable=False)

    puzzle = relationship("Puzzle", back_populates="story_entry")


class DailyPuzzle(Base):
    __tablename__ = "daily_puzzles"

    date = Column(Date, primary_key=True)
    puzzle_id = Column(UNIQUEIDENTIFIER, ForeignKey("puzzles.id"), nullable=False)

    puzzle = relationship("Puzzle", back_populates="daily_entry")


class Solve(Base):
    __tablename__ = "solves"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UNIQUEIDENTIFIER, ForeignKey("users.id"), nullable=False)
    puzzle_id = Column(UNIQUEIDENTIFIER, ForeignKey("puzzles.id"), nullable=False)

    time_seconds = Column(Integer, nullable=True)
    mistakes = Column(Integer, nullable=False, default=0)
    hints_used = Column(Integer, nullable=False, default=0)

    completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="solves")
    puzzle = relationship("Puzzle", back_populates="solves")


class DailyRanking(Base):
    __tablename__ = "daily_rankings"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))

    date = Column(Date, nullable=False)
    user_id = Column(UNIQUEIDENTIFIER, ForeignKey("users.id"), nullable=False)

    rank = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)

    user = relationship("User")


class AiHint(Base):
    __tablename__ = "ai_hints"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UNIQUEIDENTIFIER, ForeignKey("users.id"), nullable=False)
    puzzle_id = Column(UNIQUEIDENTIFIER, ForeignKey("puzzles.id"), nullable=False)

    hint_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ai_hints")
    puzzle = relationship("Puzzle", back_populates="ai_hints")
