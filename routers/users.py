from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from db import get_db
import schemas
from models.models import User, Solve
from auth.security import get_current_user

router = APIRouter()


@router.get("/me", response_model=schemas.UserProfile)
def get_me(db: Session = Depends(get_db)):  # current_user: User = Depends(get_current_user)
    """Zwraca pelny profil zalogowanego uzytkownika (nick, avatar, statystyki)."""
    # DISABLED FOR PRESENTATION - return first user
    current_user = db.query(User).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="No users in database")
    
    total_solves = db.query(func.count(Solve.id)).filter(
        Solve.user_id == current_user.id,
        Solve.completed == True
    ).scalar()
    
    return {
        "id": current_user.id,
        "login": current_user.login,
        "email": current_user.email,
        "nick": current_user.nick,
        "avatar": current_user.avatar,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login,
        "total_solves": total_solves or 0
    }


@router.patch("/me", response_model=schemas.UserPublic)
def update_me(
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db)  # current_user: User = Depends(get_current_user)
):
    """Aktualizuje dane profilu (nick, avatar)."""
    # DISABLED FOR PRESENTATION - update first user
    current_user = db.query(User).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="No users in database")
    
    if payload.nick is not None:
        current_user.nick = payload.nick
    if payload.avatar is not None:
        current_user.avatar = payload.avatar
    
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/{user_id}", response_model=schemas.UserPublicProfile)
def get_public_profile(user_id: str, db: Session = Depends(get_db)):
    """Zwraca publiczny profil uzytkownika (nick, avatar, podstawowe staty)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    total_solves = db.query(func.count(Solve.id)).filter(
        Solve.user_id == user.id,
        Solve.completed == True
    ).scalar()
    
    return {
        "id": user.id,
        "nick": user.nick,
        "avatar": user.avatar,
        "total_solves": total_solves or 0
    }
