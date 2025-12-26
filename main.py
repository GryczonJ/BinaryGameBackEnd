from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas
from  db import get_db
from models.User import User
from auth.security import hash_password, verify_password, create_access_token

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