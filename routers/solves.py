from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from db import get_db
import schemas
from models.models import User, Solve, Puzzle
from auth.security import get_current_user

router = APIRouter()


@router.post("", response_model=schemas.SolveResponse)
def submit_solve(
    payload: schemas.SolveCreate,
    db: Session = Depends(get_db)  # current_user: User = Depends(get_current_user)
):
    """
    Zapisuje lub aktualizuje rozwiazanie puzzla przez uzytkownika
    (czas, bledy, uzyte hinty, status ukonczenia).
    UPSERT: (user_id + puzzle_id)
    """
    # DISABLED FOR PRESENTATION - use first user
    current_user = db.query(User).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="No users in database")
    
    # Verify puzzle exists
    puzzle = db.query(Puzzle).filter(Puzzle.id == payload.puzzle_id).first()
    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    
    # Check if solve already exists
    existing = db.query(Solve).filter(
        Solve.user_id == current_user.id,
        Solve.puzzle_id == payload.puzzle_id
    ).first()

    if existing:
        # Update existing solve
        existing.time_seconds = payload.time_seconds
        existing.mistakes = payload.mistakes
        existing.hints_used = payload.hints_used
        existing.completed = payload.completed
        db.commit()
        db.refresh(existing)
        return {"status": "updated", "solve": existing}
    else:
        # Create new solve
        new_solve = Solve(
            user_id=current_user.id,
            puzzle_id=payload.puzzle_id,
            time_seconds=payload.time_seconds,
            mistakes=payload.mistakes,
            hints_used=payload.hints_used,
            completed=payload.completed,
            created_at=datetime.utcnow()
        )
        db.add(new_solve)
        db.commit()
        db.refresh(new_solve)
        return {"status": "created", "solve": new_solve}


@router.get("/me", response_model=list[schemas.SolvePublic])
def get_my_solves(
    db: Session = Depends(get_db)  # current_user: User = Depends(get_current_user)
):
    """Zwraca wszystkie rozwiazania zalogowanego uzytkownika."""
    # DISABLED FOR PRESENTATION - use first user
    current_user = db.query(User).first()
    if not current_user:
        return []
    solves = db.query(Solve).filter(Solve.user_id == current_user.id).all()
    return solves


@router.get("/puzzle/{puzzle_id}", response_model=schemas.SolvePublic | None)
def get_puzzle_solve(
    puzzle_id: str,
    db: Session = Depends(get_db)  # current_user: User = Depends(get_current_user)
):
    """Zwraca informacje, czy uzytkownik rozwiazal dany puzzle (postep)."""
    # DISABLED FOR PRESENTATION - use first user
    current_user = db.query(User).first()
    if not current_user:
        return None
    
    solve = db.query(Solve).filter(
        Solve.user_id == current_user.id,
        Solve.puzzle_id == puzzle_id
    ).first()
    
    if not solve:
        return None
    
    return solve
