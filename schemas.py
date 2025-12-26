from pydantic import BaseModel, EmailStr
from typing import Optional
from models.enums import PuzzleType

# Schematy dla Auth
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Schematy dla Puzzles (CRUD)
class PuzzleBase(BaseModel):
    grid_size: int
    puzzle_data: str
    solution: str
    type: PuzzleType = PuzzleType.STORY
    difficulty: Optional[int] = None

class PuzzleCreate(PuzzleBase):
    pass

class PuzzleResponse(PuzzleBase):
    id: int
    class Config:
        from_attributes = True # Pozwala mapować obiekty SQLAlchemy