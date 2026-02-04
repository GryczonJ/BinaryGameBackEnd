from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json
import os
import concurrent.futures
import random

from db import get_db
import schemas
from models.models import User, Puzzle, AiHint
from auth.security import get_current_user
from ai_model import generate_hint_text, generate_error_feedback

router = APIRouter()

AI_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_SECONDS", "30.0"))
AI_ENABLED = os.getenv("AI_ENABLED", "1").lower() not in {"0", "false", "no"}
AI_DISABLE_TIMEOUT = os.getenv("AI_DISABLE_TIMEOUT", "0").lower() in {"1", "true", "yes"}


def get_possible_moves(grid_state: str, size: int) -> list[dict]:
    """
    Analyzes the puzzle grid and returns possible next moves based on binary puzzle rules:
    1. If there's "0 _ 0" or "1 _ 1" pattern, fill gap with opposite number
    2. If row/column has size/2 of one number, remaining cells must be the other number
    """
    grid = parse_grid_state(grid_state, size)
    if not grid:
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

    # Rule 3: Check for "gap X X gap" patterns (prevents 3 consecutive)
    for row in range(size):
        for col in range(size):
            if grid[row][col] is None or grid[row][col] == "":

                # ---- Horizontal: _ X X
                if col <= size - 3:
                    a = grid[row][col + 1]
                    b = grid[row][col + 2]
                    if a == b and a is not None and a != "":
                        hints.append({
                            "row": row,
                            "col": chr(col + 65),
                            "value": 1 - a,
                            "reason": f"Prevents 3 consecutive {a}s in row {row + 1}"
                        })
                        continue

                # ---- Horizontal: X X _
                if col >= 2:
                    a = grid[row][col - 1]
                    b = grid[row][col - 2]
                    if a == b and a is not None and a != "":
                        hints.append({
                            "row": row,
                            "col": chr(col + 65),
                            "value": 1 - a,
                            "reason": f"Prevents 3 consecutive {a}s in row {row + 1}"
                        })
                        continue

                # ---- Vertical: _ X X
                if row <= size - 3:
                    a = grid[row + 1][col]
                    b = grid[row + 2][col]
                    if a == b and a is not None and a != "":
                        hints.append({
                            "row": row,
                            "col": chr(col + 65),
                            "value": 1 - a,
                            "reason": f"Prevents 3 consecutive {a}s in column {col + 1}"
                        })
                        continue

                # ---- Vertical: X X _
                if row >= 2:
                    a = grid[row - 1][col]
                    b = grid[row - 2][col]
                    if a == b and a is not None and a != "":
                        hints.append({
                            "row": row,
                            "col": chr(col + 65),
                            "value": 1 - a,
                            "reason": f"Prevents 3 consecutive {a}s in column {col + 1}"
                        })
                        continue

    random.shuffle(hints)
    
    return hints


def parse_grid_state(grid_state: str, size: int) -> list[list[int | None]] | None:
    if not grid_state:
        return None
    # JSON format?
    if grid_state.strip().startswith("["):
        try:
            parsed = json.loads(grid_state)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    # Flat string format "0/1/."
    flat = grid_state.strip()
    if size <= 0 or size * size != len(flat):
        size = int(len(flat) ** 0.5) if flat else 0
    if size <= 0 or size * size != len(flat):
        return None
    grid: list[list[int | None]] = []
    for r in range(size):
        row: list[int | None] = []
        for c in range(size):
            ch = flat[r * size + c]
            if ch == "0":
                row.append(0)
            elif ch == "1":
                row.append(1)
            else:
                row.append(None)
        grid.append(row)
    return grid


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
    
    # Verify puzzle exists
    puzzle = db.query(Puzzle).filter(Puzzle.id == payload.puzzle_id).first()
    
    # Determine grid size - default to 6 if puzzle not found
    puzzle_size = puzzle.size if puzzle else 6
    
    # Get possible moves using function calling
    possible_hints = get_possible_moves(payload.grid_state, puzzle_size)
    
    # Use AI model to generate natural language hint (with optional timeout)
    grid_for_ai = json.dumps(parse_grid_state(payload.grid_state, puzzle_size)) if payload.grid_state else payload.grid_state
    hint_text = None

    if AI_ENABLED:
        try:
            if AI_DISABLE_TIMEOUT:
                hint_text = generate_hint_text(grid=grid_for_ai, hints=possible_hints)
            else:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(generate_hint_text, grid=grid_for_ai, hints=possible_hints)
                    hint_text = future.result(timeout=AI_TIMEOUT_SECONDS)
        except (FileNotFoundError, concurrent.futures.TimeoutError, RuntimeError, ValueError):
            hint_text = None
            print("AI hint generation failed or timed out.")

    if not hint_text:
        hint_text = "Hmm, hats a tough one... i dunno."
        print("AI hint: FALLBACK")
    else:
        print("AI hint: MODEL")
    
    # Save hint to database (only if both user and puzzle exist)
    if current_user and puzzle:
        ai_hint = AiHint(
            user_id=current_user.id,
            puzzle_id=payload.puzzle_id,
            hint_text=hint_text,
            created_at=datetime.utcnow()
        )
        db.add(ai_hint)
        db.commit()
        
        hints_used = db.query(AiHint).filter(
            AiHint.user_id == current_user.id,
            AiHint.puzzle_id == payload.puzzle_id
        ).count()
    else:
        hints_used = 0
    
    return {
        "hint": hint_text,
        "hints_used_total": hints_used
    }


@router.post("/error-feedback", response_model=schemas.AiErrorFeedback)
def get_error_feedback(
    payload: schemas.AiErrorResponse,
    db: Session = Depends(get_db)
):
    """
    Generuje przyjazna wiadomosc od AI wyjasnniajaca bledy ktore popelnil uzytkownik.
    Przyjmuje aktualny wyglad puzzla i liste bledow, a AI model generuje
    przyjazna wiadomosc wyjasnniajaca jakie reguly zostaly naruszone.
    """
    # DISABLED FOR PRESENTATION - use first user (optional)
    current_user = db.query(User).first()
    
    if not payload.errors:
        return {
            "message": "Great! No errors detected in this move.",
            "errors_corrected": 0
        }
    
    # Use AI model to generate natural language error feedback (with optional timeout)
    grid_for_ai = json.dumps(parse_grid_state(payload.grid_state, 0)) if payload.grid_state else payload.grid_state
    feedback_text = None

    if AI_ENABLED:
        try:
            if AI_DISABLE_TIMEOUT:
                feedback_text = generate_error_feedback(grid=grid_for_ai, errors=payload.errors)
            else:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(generate_error_feedback, grid=grid_for_ai, errors=payload.errors)
                    feedback_text = future.result(timeout=AI_TIMEOUT_SECONDS)
        except (FileNotFoundError, concurrent.futures.TimeoutError, RuntimeError, ValueError):
            print("AI error feedback generation failed or timed out.")
            feedback_text = None
    if not feedback_text:
        error_count = len(payload.errors)
        feedback_text = f"Oops! I see you made {error_count} mistake(s). But i cannot figure out what they are..."
        print("AI error feedback: FALLBACK")
    else:
        print("AI error feedback: MODEL")
    return {
        "message": feedback_text,
        "errors_corrected": len(payload.errors)
    }
