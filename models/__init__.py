# Importujemy Base, aby był dostępny jako models.Base
from db import Base

# Importujemy wszystkie klasy modeli, aby SQLAlchemy zarejestrowało je w Base.metadata
from .PuzzleType import PuzzleType
from .User import User
from .Puzzle import Puzzle
from .Solution import Solution
from .Ranking import Ranking
from .models import HintLog
from .DailyPuzzle import DailyPuzzle


# Opcjonalnie: definiujemy co ma być dostępne przy "from models import *"
__all__ = [
    "Base",
    "User",
    "Puzzle",
    "Solution",
    "Ranking",
    "HintLog",
    "DailyPuzzle"
]