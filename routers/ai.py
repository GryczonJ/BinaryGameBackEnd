from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json

from db import get_db
import schemas
from models.models import User, Puzzle, AiHint
from auth.security import get_current_user

router = APIRouter()


def get_possible_moves(grid_state: str, size: int) -> list[dict]:
    """
    Function calling dla AI - zwraca mozliwe ruchy dla aktualnego stanu puzzla.
    Format grid_state: JSON string reprezentujacy 2D array
    """
    try:
        grid = json.loads(grid_state)
    except:
        return []
    
    possible_moves = []
    
    # Find empty cells and suggest valid moves
    for row in range(size):
        for col in range(size):
            if grid[row][col] is None or grid[row][col] == "":
                # Check what values are possible here
                # This is simplified - in production, implement full binary puzzle rules
                possible_moves.append({
                    "row": row,
                    "col": col,
                    "possible_values": [0, 1],
                    "reason": "Empty cell"
                })
    
    return possible_moves[:5]  # Limit to 5 suggestions


@router.post("/hint", response_model=schemas.AiHintResponse)
def get_hint(
    payload: schemas.AiHintRequest,
    db: Session = Depends(get_db)  # current_user: User = Depends(get_current_user)
):
    """
    Generuje tekstowa podpowiedz dla aktualnego stanu puzzla.
    Przyjmuje aktualny wyglad puzzla, wykonuje function calling ktory zwroci
    possible moves, i potem AI model na bazie odpowiedzi z funkcji ladnie ubiera to w slowa.
    Zapisuje hint w bazie danych.
    """
    # DISABLED FOR PRESENTATION - use first user
    current_user = db.query(User).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="No users in database")
    
    # Verify puzzle exists
    puzzle = db.query(Puzzle).filter(Puzzle.id == payload.puzzle_id).first()
    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    
    # Get possible moves using function calling
    possible_moves = get_possible_moves(payload.grid_state, puzzle.size)
    
    if not possible_moves:
        hint_text = "Nie znalazlem zadnych oczywistych ruchow. Sprawdz zasady gry!"
    else:
        # Generate hint text based on possible moves
        # In production, this would call an actual AI model
        move = possible_moves[0]
        hint_text = f"Sprobuj spojrzec na wiersz {move['row'] + 1}, kolumne {move['col'] + 1}. "
        hint_text += "Sprawdz, czy nie ma juz za duzo jedynek lub zer w tym wierszu lub kolumnie."
    
    # Save hint to database
    ai_hint = AiHint(
        user_id=current_user.id,
        puzzle_id=payload.puzzle_id,
        hint_text=hint_text,
        created_at=datetime.utcnow()
    )
    db.add(ai_hint)
    db.commit()
    
    return {
        "hint": hint_text,
        "hints_used_total": db.query(AiHint).filter(
            AiHint.user_id == current_user.id,
            AiHint.puzzle_id == payload.puzzle_id
        ).count()
    }
