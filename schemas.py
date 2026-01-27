from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import date, datetime


# ==================== AUTH SCHEMAS ====================
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    login: str
    email: EmailStr
    password: str
    nick: str | None = None


class UserLogin(BaseModel):
    login_or_email: str
    password: str


class UserCheck(BaseModel):
    identifier: str  # email or login


class UserCheckResponse(BaseModel):
    exists: bool
    message: str | None = None


# ==================== USER SCHEMAS ====================
class UserPublic(BaseModel):
    id: UUID
    nick: str | None = None
    avatar: str | None = None  # Base64 image data

    model_config = ConfigDict(from_attributes=True)


class UserProfile(BaseModel):
    id: UUID
    login: str
    email: str
    nick: str | None = None
    avatar: str | None = None  # Base64 image data
    created_at: datetime | None = None
    last_login: datetime | None = None
    total_solves: int = 0

    model_config = ConfigDict(from_attributes=True)


class UserPublicProfile(BaseModel):
    id: UUID
    nick: str | None = None
    avatar: str | None = None  # Base64 image data
    total_solves: int = 0


class UserUpdate(BaseModel):
    nick: str | None = None
    avatar: str | None = None  # Base64 image data


# ==================== PUZZLE SCHEMAS ====================
class PuzzlePublic(BaseModel):
    id: UUID | str
    type: str
    difficulty: int
    size: int
    grid_initial: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PuzzleCreate(BaseModel):
    type: str
    difficulty: int
    size: int
    grid_solution: str
    grid_initial: str


class PuzzleUpdate(BaseModel):
    difficulty: int | None = None
    grid_solution: str | None = None
    grid_initial: str | None = None


# ==================== SOLVE SCHEMAS ====================
class SolveCreate(BaseModel):
    puzzle_id: UUID
    time_seconds: int | None = None
    mistakes: int = 0
    hints_used: int = 0
    completed: bool = True


class SolvePublic(BaseModel):
    id: UUID
    user_id: UUID
    puzzle_id: UUID
    time_seconds: int | None = None
    mistakes: int
    hints_used: int
    completed: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SolveResponse(BaseModel):
    status: str
    solve: SolvePublic


# ==================== RANKING SCHEMAS ====================
class DailyRankingPublic(BaseModel):
    rank: int
    user_id: UUID
    user_nick: str | None = None
    score: int
    mistakes: int
    hints_used: int
    time_seconds: int | None = None


class UserRankingHistory(BaseModel):
    date: date
    rank: int
    score: int
    total_participants: int


# ==================== CALENDAR SCHEMAS ====================
class CalendarDay(BaseModel):
    date: date
    participated: bool
    medal: str | None = None


# ==================== AI HINT SCHEMAS ====================
class AiHintRequest(BaseModel):
    puzzle_id: UUID
    grid_state: str  # JSON string representing current grid state


class AiHintResponse(BaseModel):
    hint: str
    hints_used_total: int


# ==================== ADMIN SCHEMAS ====================
class DailyPuzzleAssign(BaseModel):
    puzzle_id: UUID


class StoryPuzzleAssign(BaseModel):
    order_index: int


class DailyRankingRow(BaseModel):
    user_id: UUID
    rank: int
    score: int
