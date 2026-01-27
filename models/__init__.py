# Importujemy Base, aby byl dostepny jako models.Base
from db import Base

# Importujemy wszystkie klasy modeli z models.py
from .models import User, Session, Puzzle, StoryPuzzle, DailyPuzzle, Solve, DailyRanking, AiHint


# Opcjonalnie: definiujemy co ma byc dostepne przy "from models import *"
__all__ = [
    "Base",
    "User",
    "Session",
    "Puzzle",
    "StoryPuzzle",
    "DailyPuzzle",
    "Solve",
    "DailyRanking",
    "AiHint"
]