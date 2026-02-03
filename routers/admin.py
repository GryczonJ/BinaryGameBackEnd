from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
import uuid

from db import get_db
import schemas
from models.models import User, Puzzle, DailyPuzzle, StoryPuzzle
from auth.security import get_current_user
from puzzles import generate_binary_puzzle
from story_levels import STORY_LEVELS

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


@router.post("/daily/generate-missing")
def generate_missing_daily_puzzles(
    db: Session = Depends(get_db)  # current_user: User = Depends(get_current_user)
):
    """Generuje brakujace daily puzzles od 2026-01-01 do dzis + 7 dni."""
    start_date = date(2026, 1, 1)
    end_date = date.today() + timedelta(days=7)

    created = 0
    skipped = 0

    current_date = start_date
    while current_date <= end_date:
        exists = db.query(DailyPuzzle).filter(DailyPuzzle.date == current_date).first()
        if exists:
            skipped += 1
            current_date += timedelta(days=1)
            continue

        solution, initial = generate_binary_puzzle(size=6, fullness=50)
        puzzle = Puzzle(
            id=str(uuid.uuid4()),
            type="daily",
            difficulty=3,
            size=6,
            grid_solution=solution,
            grid_initial=initial,
            created_at=datetime.utcnow()
        )
        db.add(puzzle)
        db.flush()
        daily_puzzle = DailyPuzzle(
            date=current_date,
            puzzle_id=puzzle.id
        )
        db.add(daily_puzzle)
        created += 1
        current_date += timedelta(days=1)

    db.commit()
    return {
        "status": "ok",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "created": created,
        "skipped": skipped
    }


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


@router.post("/story/populate")
def populate_story_mode(
    db: Session = Depends(get_db)  # current_user: User = Depends(get_current_user)
):
    """Dodaje 6 predefiniowanych poziomow story (idempotentnie)."""
    created = 0
    updated = 0
    skipped = 0

    for idx, level in enumerate(STORY_LEVELS, start=1):
        story_entry = db.query(StoryPuzzle).filter(StoryPuzzle.order_index == idx).first()
        if story_entry:
            puzzle = db.query(Puzzle).filter(Puzzle.id == story_entry.puzzle_id).first()
            if not puzzle:
                puzzle = Puzzle(
                    id=str(uuid.uuid4()),
                    type="story",
                    difficulty=level.difficulty,
                    size=level.size,
                    grid_solution=level.grid_initial,
                    grid_initial=level.grid_initial,
                    created_at=datetime.utcnow()
                )
                db.add(puzzle)
                db.flush()
                story_entry.puzzle_id = puzzle.id
                updated += 1
            else:
                changed = False
                if puzzle.type != "story":
                    puzzle.type = "story"
                    changed = True
                if puzzle.size != level.size:
                    puzzle.size = level.size
                    changed = True
                if puzzle.difficulty != level.difficulty:
                    puzzle.difficulty = level.difficulty
                    changed = True
                if puzzle.grid_initial != level.grid_initial:
                    puzzle.grid_initial = level.grid_initial
                    changed = True
                if puzzle.grid_solution != level.grid_initial:
                    puzzle.grid_solution = level.grid_initial
                    changed = True
                if changed:
                    updated += 1
                else:
                    skipped += 1
            continue

        puzzle = Puzzle(
            id=str(uuid.uuid4()),
            type="story",
            difficulty=level.difficulty,
            size=level.size,
            grid_solution=level.grid_initial,
            grid_initial=level.grid_initial,
            created_at=datetime.utcnow()
        )
        db.add(puzzle)
        db.flush()
        story_puzzle = StoryPuzzle(
            id=str(uuid.uuid4()),
            puzzle_id=puzzle.id,
            order_index=idx
        )
        db.add(story_puzzle)
        created += 1

    db.commit()
    return {
        "status": "ok",
        "created": created,
        "updated": updated,
        "skipped": skipped
    }


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
