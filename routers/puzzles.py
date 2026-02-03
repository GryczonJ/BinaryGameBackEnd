from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
import random

from db import get_db
import schemas
from models.models import Puzzle, StoryPuzzle, DailyPuzzle
from puzzles import generate_binary_puzzle

router = APIRouter()


@router.get("/story", response_model=list[schemas.PuzzlePublic])
def get_story_puzzles(db: Session = Depends(get_db)):
    """Zwraca liste puzzli trybu story w kolejnosci."""
    story_puzzles = db.query(StoryPuzzle).order_by(StoryPuzzle.order_index).all()
    puzzles = []
    for sp in story_puzzles:
        puzzle = db.query(Puzzle).filter(Puzzle.id == sp.puzzle_id).first()
        if puzzle:
            puzzles.append(puzzle)
    return puzzles


@router.get("/story/{puzzle_id}", response_model=schemas.PuzzlePublic)
def get_story_puzzle(puzzle_id: str, db: Session = Depends(get_db)):
    """Zwraca pojedynczy puzzle story (grid poczatkowy)."""
    puzzle = db.query(Puzzle).filter(
        Puzzle.id == puzzle_id,
        Puzzle.type == "story"
    ).first()
    if not puzzle:
        raise HTTPException(status_code=404, detail="Story puzzle not found")
    return puzzle


@router.get("/daily/today", response_model=schemas.PuzzlePublic)
def get_daily_today(db: Session = Depends(get_db)):
    """Zwraca dzisiejszy daily puzzle."""
    today = datetime.utcnow().date()
    dp = db.query(DailyPuzzle).filter(DailyPuzzle.date == today).first()
    if not dp:
        raise HTTPException(status_code=404, detail="Brak daily puzzle na dzis")
    puzzle = db.query(Puzzle).filter(Puzzle.id == dp.puzzle_id).first()
    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle nie istnieje")
    return puzzle


@router.get("/daily/{date}", response_model=schemas.PuzzlePublic)
def get_daily_by_date(date: str, db: Session = Depends(get_db)):
    """Zwraca daily puzzle dla konkretnej daty."""
    try:
        puzzle_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    dp = db.query(DailyPuzzle).filter(DailyPuzzle.date == puzzle_date).first()
    if not dp:
        raise HTTPException(status_code=404, detail="Brak daily puzzle na ta date")
    
    puzzle = db.query(Puzzle).filter(Puzzle.id == dp.puzzle_id).first()
    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle nie istnieje")
    return puzzle


@router.get("/random", response_model=schemas.PuzzlePublic)
def get_random_puzzle(
    size: int = 6,
    fullness: int = 50,
    difficulty: int | None = None,
    db: Session = Depends(get_db)
):
    """Generuje i zwraca losowy puzzle (zapisany do bazy).
    
    Args:
        size: Board size (4, 6, 8, or 10). Default: 6
        fullness: 0-100, percentage of filled cells (0=empty, 100=full). Default: 50
                  Recommended range: 20-80 for playable puzzles
    """
    if size%2 != 0:
        raise HTTPException(status_code=400, detail="Size must be an even number")
    if not (0 <= fullness <= 100):
        raise HTTPException(status_code=400, detail="Fullness must be between 0 and 100")
    
    solution, initial = generate_binary_puzzle(size, fullness)

    new_puzzle = Puzzle(
        type="random",
        difficulty=difficulty or (size // 2),
        size=size,
        grid_solution=solution,
        grid_initial=initial,
        created_at=datetime.utcnow()
    )
    db.add(new_puzzle)
    db.commit()
    db.refresh(new_puzzle)
    return new_puzzle
