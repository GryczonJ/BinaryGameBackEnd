from datetime import datetime, timedelta
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from db import get_db
from models import User, Session as DbSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
MAX_PASSWORD_BYTES = 1024


def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is too long (max 1024 bytes).",
        )
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if len(plain_password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        return False
    return pwd_context.verify(plain_password, hashed_password)

def new_session_token() -> str:
    return secrets.token_urlsafe(32)

def create_session(db: Session, user: User, days: int = 30) -> str:
    token = new_session_token()
    expires_at = datetime.utcnow() + timedelta(days=days)

    s = DbSession(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.add(s)
    db.commit()
    return token

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    now = datetime.utcnow()

    sess = db.query(DbSession).filter(
        DbSession.token == token,
        DbSession.expires_at > now
    ).first()

    if not sess:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == sess.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
