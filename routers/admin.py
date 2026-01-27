from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from db import get_db
import schemas
from models.models import User, Puzzle, DailyPuzzle, StoryPuzzle
from auth.security import get_current_user

router = APIRouter()


# Note: In production, add admin role check to get_current_user
# For now, any authenticated user can access admin endpoints


@router.post("/puzzles", response_model=schemas.PuzzlePublic)
def create_puzzle(
    payload: schemas.PuzzleCreate,
    db: Session = Depends(get_db)  # current_user: User = Depends(get_current_user)
):
    """Dodaje nowy puzzle do bazy."""
    puzzle = Puzzle(
        id=str(uuid.uuid4()),
        type=payload.type,
        difficulty=payload.difficulty,
        size=payload.size,
        grid_solution=payload.grid_solution,
        grid_initial=payload.grid_initial,
        created_at=datetime.utcnow()
    )
    db.add(puzzle)
    db.commit()
    db.refresh(puzzle)
    return puzzle


@router.patch("/puzzles/{puzzle_id}", response_model=schemas.PuzzlePublic)
def update_puzzle(
    puzzle_id: str,
    payload: schemas.PuzzleUpdate,
    db: Session = Depends(get_db)  # current_user: User = Depends(get_current_user)
):
    """Edytuje istniejacy puzzle."""
    puzzle = db.query(Puzzle).filter(Puzzle.id == puzzle_id).first()
    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    
    if payload.difficulty is not None:
        puzzle.difficulty = payload.difficulty
    if payload.grid_solution is not None:
        puzzle.grid_solution = payload.grid_solution
    if payload.grid_initial is not None:
        puzzle.grid_initial = payload.grid_initial
    
    db.commit()
    db.refresh(puzzle)
    return puzzle


@router.delete("/puzzles/{puzzle_id}")
def delete_puzzle(
    puzzle_id: str,
    db: Session = Depends(get_db)  # current_user: User = Depends(get_current_user)
):
    """Usuwa puzzle z bazy."""
    puzzle = db.query(Puzzle).filter(Puzzle.id == puzzle_id).first()
    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    
    db.delete(puzzle)
    db.commit()
    return {"status": "deleted"}


@router.post("/daily/{date}")
def set_daily_puzzle(
    date: str,
    payload: schemas.DailyPuzzleAssign,
    db: Session = Depends(get_db)  # current_user: User = Depends(get_current_user)
):
    """Przypisuje konkretny puzzle jako daily puzzle na dana date."""
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Verify puzzle exists
    puzzle = db.query(Puzzle).filter(Puzzle.id == payload.puzzle_id).first()
    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    
    # Check if daily puzzle already exists for this date
    existing = db.query(DailyPuzzle).filter(DailyPuzzle.date == date_obj).first()
    if existing:
        existing.puzzle_id = payload.puzzle_id
    else:
        daily_puzzle = DailyPuzzle(
            date=date_obj,
            puzzle_id=payload.puzzle_id
        )
        db.add(daily_puzzle)
    
    db.commit()
    return {"status": "assigned", "date": date_obj, "puzzle_id": payload.puzzle_id}


@router.post("/story/{puzzle_id}")
def add_story_puzzle(
    puzzle_id: str,
    payload: schemas.StoryPuzzleAssign,
    db: Session = Depends(get_db)  # current_user: User = Depends(get_current_user)
):
    """Dodaje puzzle do story mode z okreslonym order_index."""
    # Verify puzzle exists
    puzzle = db.query(Puzzle).filter(Puzzle.id == puzzle_id).first()
    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    
    story_puzzle = StoryPuzzle(
        id=str(uuid.uuid4()),
        puzzle_id=puzzle_id,
        order_index=payload.order_index
    )
    db.add(story_puzzle)
    db.commit()
    return {"status": "added", "puzzle_id": puzzle_id, "order_index": payload.order_index}
