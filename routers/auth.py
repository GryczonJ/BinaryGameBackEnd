from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import base64

from db import get_db
import schemas
from models.models import User, Session as DbSession
from auth.security import hash_password, verify_password, create_session, get_current_user

router = APIRouter()

MAX_AVATAR_BYTES = 500 * 1024


def normalize_email(value: str) -> str:
    return value.strip().lower()


def normalize_login(value: str) -> str:
    return value.strip()


def normalize_avatar(value: str | None, seed: str) -> str:
    if value:
        trimmed = value.strip()
        if trimmed.startswith("data:image/") and "," in trimmed:
            _, b64 = trimmed.split(",", 1)
            if not b64:
                raise HTTPException(status_code=400, detail="Invalid avatar data.")
            approx_bytes = int(len(b64) * 3 / 4)
            if approx_bytes > MAX_AVATAR_BYTES:
                raise HTTPException(status_code=400, detail="Avatar is too large.")
            return trimmed
        raise HTTPException(status_code=400, detail="Avatar must be base64 data URL.")

    # fallback svg avatar
    initials = (seed.strip()[:2] or "BG").upper()
    svg = f"<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><rect width='100%' height='100%' fill='#2b2b2b'/><text x='50%' y='54%' text-anchor='middle' font-family='Arial' font-size='72' fill='#ffffff'>{initials}</text></svg>"
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


@router.post("/check", response_model=schemas.UserCheckResponse)
def check_user_exists(payload: schemas.UserCheck, db: Session = Depends(get_db)):
    """Sprawdza czy uzytkownik istnieje (po email lub login)."""
    identifier = payload.identifier.strip()
    if "@" in identifier:
        email = normalize_email(identifier)
        user = db.query(User).filter(User.email == email).first()
    else:
        login = normalize_login(identifier)
        user = db.query(User).filter(User.login == login).first()
    
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
    login = normalize_login(payload.login)
    email = normalize_email(payload.email)

    if db.query(User).filter(User.login == login).first():
        raise HTTPException(status_code=400, detail="Login zajety")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email zajety")

    avatar = normalize_avatar(payload.avatar_url, payload.nick or login)
    
    user = User(
        login=login,
        email=email,
        password_hash=hash_password(payload.password),
        nick=payload.nick,
        avatar=avatar,
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
    identifier = payload.login_or_email.strip()
    if "@" in identifier:
        email = normalize_email(identifier)
        user = db.query(User).filter(User.email == email).first()
    else:
        login = normalize_login(identifier)
        user = db.query(User).filter(User.login == login).first()

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


@router.post("/forgot", response_model=schemas.ForgotPasswordResponse)
def forgot_password(payload: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    identifier = payload.identifier.strip()
    if "@" in identifier:
        email = normalize_email(identifier)
        user = db.query(User).filter(User.email == email).first()
    else:
        login = normalize_login(identifier)
        user = db.query(User).filter(User.login == login).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password("")
    db.commit()
    return {"message": "Password reset to empty string."}


@router.post("/change-password", response_model=schemas.ChangePasswordResponse)
def change_password(payload: schemas.ChangePasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No users in database")
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Old password incorrect")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password changed."}
