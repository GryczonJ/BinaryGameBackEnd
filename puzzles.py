from fastapi import APIRouter, Depends, HTTPException
import schemas, models.Puzzle as models_p
from typing import List
from  db import get_db
from security import get_current_user, admin_required
from auth.security import hash_password, verify_password, create_access_token
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas
from db import get_db  # Importujemy gotową funkcję z Twojego pliku db.py
from models.User import User
import models.Puzzle as models_p   # FIX: Dodany brakujący alias
import models.Solution as models_s
from models.PuzzleType import PuzzleType

router = APIRouter(prefix="/puzzles", tags=["Puzzles"])


@router.get("/", response_model=List[schemas.PuzzleResponse])
def get_puzzles(database: Session = Depends(get_db), user=Depends(get_current_user)):
    return database.query(models_p.Puzzle).all()

@router.get("/{id}", response_model=schemas.PuzzleResponse)
def get_puzzle(id: int, database: Session = Depends(get_db), user=Depends(get_current_user)):
    puzzle = database.query(models_p.Puzzle).filter(models_p.Puzzle.id == id).first()
    if not puzzle:
        raise HTTPException(status_code=404, detail="Zagadka nie istnieje")
    return puzzle

@router.post("/", response_model=schemas.PuzzleResponse)
def create_puzzle(puzzle_in: schemas.PuzzleCreate, database: Session = Depends(get_db), admin=Depends(admin_required)):
    new_puzzle = models_p.Puzzle(**puzzle_in.dict())
    database.add(new_puzzle)
    database.commit()
    database.refresh(new_puzzle)
    return new_puzzle

@router.put("/{id}")
def update_puzzle(id: int, puzzle_in: schemas.PuzzleCreate, database: Session = Depends(get_db), admin=Depends(admin_required)):
    puzzle = database.query(models_p.Puzzle).filter(models_p.Puzzle.id == id).first()
    if not puzzle: raise HTTPException(status_code=404)
    
    for key, value in puzzle_in.dict().items():
        setattr(puzzle, key, value)
    database.commit()
    return {"message": "Updated"}

@router.delete("/{id}")
def delete_puzzle(id: int, database: Session = Depends(get_db), admin=Depends(admin_required)):
    database.query(models_p.Puzzle).filter(models_p.Puzzle.id == id).delete()
    database.commit()
    return {"message": "Deleted"}