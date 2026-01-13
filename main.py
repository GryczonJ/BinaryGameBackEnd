from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas
from  db import get_db

import models.Solution as models_s
from models.User import User
from models.PuzzleType import PuzzleType
#from auth.security import hash_password, verify_password, create_access_token
#from security import get_current_user, admin_required
import models.Puzzle as models_p
from auth.security import get_current_user, admin_required


app = FastAPI()

@app.post("/auth/register", response_model=schemas.Token)
def register(user_in: schemas.UserCreate, database: Session = Depends(get_db)):
    # 1. Sprawdź czy mail zajęty
    user_exists = database.query(User).filter(User.email == user_in.email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Ten email jest już w bazie.")

    # 2. Szyfrowanie hasła (bcrypt)
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hash_password(user_in.password), # Funkcja z poprzedniego kroku
        role="user"
    )
    
    database.add(new_user)
    database.commit()
    database.refresh(new_user)
    
    # 3. Od razu po rejestracji dajemy token (opcjonalnie)
    token = create_access_token(data={"sub": new_user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/auth/login")
def login(user_in: schemas.UserLogin, database: Session = Depends(get_db)):
    user = database.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Niepoprawny email lub hasło")
    
    token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

import models.Solution as models_s
from models.PuzzleType import PuzzleType

@app.get("/story/next")
def get_next_story_puzzle(database: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # 1. Pobierz ID wszystkich rozwiązanych zagadek przez tego użytkownika
    solved_ids = database.query(models_s.Solution.puzzle_id).filter(
        models_s.Solution.user_id == current_user.id
    ).all()
    solved_ids_list = [r[0] for r in solved_ids]

    # 2. Znajdź pierwszą zagadkę typu STORY, której nie ma w rozwiązanych
    next_puzzle = database.query(models_p.Puzzle).filter(
        models_p.Puzzle.type == PuzzleType.STORY,
        ~models_p.Puzzle.id.in_(solved_ids_list)
    ).order_by(models_p.Puzzle.id.asc()).first()

    if not next_puzzle:
        return {"message": "Gratulacje! Rozwiązałeś wszystkie zagadki story mode."}
    
    return next_puzzle

@app.get("/auth/me")
def read_users_me(current_user = Depends(get_current_user)):
    return current_user

@app.post("/puzzles")
def add_puzzle(puzzle: schemas.PuzzleCreate, admin = Depends(admin_required)):
    # Jeśli kod tu dotrze, mamy pewność, że to admin
    return {"status": "added by admin"}