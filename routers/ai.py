from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json

from db import get_db
import schemas
from models.models import User, Puzzle, AiHint
from auth.security import get_current_user
from ai_model import generate_hint_text

router = APIRouter()


def get_possible_moves(grid_state: str, size: int) -> list[dict]:
    """
    Analyzes the puzzle grid and returns possible next moves based on binary puzzle rules:
    1. If there's "0 _ 0" or "1 _ 1" pattern, fill gap with opposite number
    2. If row/column has size/2 of one number, remaining cells must be the other number
    """
    try:
        grid = json.loads(grid_state)
    except:
        return []
    
    hints = []
    
    # Helper function to count values in a list
    def count_values(cells):
        zeros = sum(1 for c in cells if c == 0)
        ones = sum(1 for c in cells if c == 1)
        return zeros, ones
    
    # Rule 1: Check for "X gap X" patterns (prevents 3 consecutive)
    for row in range(size):
        for col in range(size):
            if grid[row][col] is None or grid[row][col] == "":
                # Check horizontal pattern: X _ X
                if col >= 1 and col < size - 1:
                    left = grid[row][col - 1]
                    right = grid[row][col + 1]
                    if left == right and left is not None and left != "":
                        hints.append({
                            "row": row,
                            "col": chr(col+65),
                            "value": 1 - left,  # opposite value
                            "reason": f"Prevents 3 consecutive {left}s in row {row + 1}"
                        })
                        continue
                
                # Check vertical pattern: X _ X
                if row >= 1 and row < size - 1:
                    top = grid[row - 1][col]
                    bottom = grid[row + 1][col]
                    if top == bottom and top is not None and top != "":
                        hints.append({
                            "row": row,
                            "col": chr(col+65),
                            "value": 1 - top,  # opposite value
                            "reason": f"Prevents 3 consecutive {top}s in column {col + 1}"
                        })
                        continue
    
    # Rule 2: Check if row/column already has size/2 of one number
    for row in range(size):
        row_cells = grid[row]
        zeros, ones = count_values(row_cells)
        half = size // 2
        
        if zeros == half:  # Row is full of zeros, remaining must be 1s
            for col in range(size):
                if grid[row][col] is None or grid[row][col] == "":
                    hints.append({
                        "row": row,
                        "col": chr(col+65),
                        "value": 1,
                        "reason": f"Row {row + 1} already has {half} zeros, remaining cells must be 1s"
                    })
        elif ones == half:  # Row is full of ones, remaining must be 0s
            for col in range(size):
                if grid[row][col] is None or grid[row][col] == "":
                    hints.append({
                        "row": row,
                        "col": chr(col+65),
                        "value": 0,
                        "reason": f"Row {row + 1} already has {half} ones, remaining cells must be 0s"
                    })
    
    # Check columns
    for col in range(size):
        col_cells = [grid[row][col] for row in range(size)]
        zeros, ones = count_values(col_cells)
        half = size // 2
        
        if zeros == half:  # Column is full of zeros, remaining must be 1s
            for row in range(size):
                if grid[row][col] is None or grid[row][col] == "":
                    hints.append({
                        "row": row,
                        "col": chr(col+65),
                        "value": 1,
                        "reason": f"Column {col + 1} already has {half} zeros, remaining cells must be 1s"
                    })
        elif ones == half:  # Column is full of ones, remaining must be 0s
            for row in range(size):
                if grid[row][col] is None or grid[row][col] == "":
                    hints.append({
                        "row": row,
                        "col": chr(col+65),
                        "value": 0,
                        "reason": f"Column {col + 1} already has {half} ones, remaining cells must be 0s"
                    })
    
    # Remove duplicates (same cell might be suggested by multiple rules)
    seen = set()
    unique_hints = []
    for hint in hints:
        key = (hint["row"], hint["col"])
        if key not in seen:
            seen.add(key)
            unique_hints.append(hint)
    
    return unique_hints[:5]  # Return top 5 hints


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
    possible_hints = get_possible_moves(payload.grid_state, puzzle.size)
    
    if not possible_hints:
        hint_text = "No obvious moves found. Double-check the puzzle rules!"
    else:
        # Use AI model to generate natural language hint
        try:
            hint_text = generate_hint_text(grid=payload.grid_state, hints=possible_hints)
        except FileNotFoundError as e:
            # Fallback if model not downloaded yet
            hint = possible_hints[0]
            hint_text = f"💡 Hint: Put {hint['value']} at row {hint['row'] + 1}, column {hint['col'] + 1}. "
            hint_text += f"Reason: {hint['reason']}"
    
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
