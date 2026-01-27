from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from db import get_db
import schemas
from models.models import User, Session as DbSession
from auth.security import hash_password, verify_password, create_session, get_current_user

router = APIRouter()


@router.post("/check", response_model=schemas.UserCheckResponse)
def check_user_exists(payload: schemas.UserCheck, db: Session = Depends(get_db)):
    """Sprawdza czy uzytkownik istnieje (po email lub login)."""
    user = db.query(User).filter(
        (User.login == payload.identifier) | (User.email == payload.identifier)
    ).first()
    
    if user:
        return {
            "exists": True,
            "message": "User exists"
        }
    else:
        return {
            "exists": False,
            "message": "User not found"
        }


@router.post("/register", response_model=schemas.Token)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    """Rejestruje nowego uzytkownika i tworzy pierwsza sesje."""
    if db.query(User).filter(User.login == payload.login).first():
        raise HTTPException(status_code=400, detail="Login zajety")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email zajety")

    # Generate default avatar if not provided
    default_avatar = f"https://ui-avatars.com/api/?name={payload.nick or payload.login}&background=random&size=200"
    
    user = User(
        login=payload.login,
        email=payload.email,
        password_hash=hash_password(payload.password),
        nick=payload.nick,
        avatar=default_avatar,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_session(db, user)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    """Logowanie (login lub email + haslo). Tworzy nowa sesje i zwraca token."""
    user = db.query(User).filter(
        (User.login == payload.login_or_email) | (User.email == payload.login_or_email)
    ).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Niepoprawne dane logowania")

    user.last_login = datetime.utcnow()
    db.commit()

    token = create_session(db, user)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
def logout(db: Session = Depends(get_db)):  # current_user: User = Depends(get_current_user)
    """Usuwa aktualna sesje (uniewaznia token)."""
    # DISABLED FOR PRESENTATION
    return {"status": "logged out (auth disabled)"}
    # # Token is in the dependency, we need to get it from the request
    # from fastapi.security import OAuth2PasswordBearer
    # from fastapi import Request
    # 
    # # We'll delete all active sessions for this user for simplicity
    # # In production, you'd want to track the specific token
    # db.query(DbSession).filter(DbSession.user_id == current_user.id).delete()
    # db.commit()
    # return {"status": "logged out"}


@router.get("/me", response_model=schemas.UserPublic)
def me(db: Session = Depends(get_db)):  # current_user: User = Depends(get_current_user)
    """Zwraca dane aktualnie zalogowanego uzytkownika."""
    # DISABLED FOR PRESENTATION - return first user
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No users in database")
    return user
