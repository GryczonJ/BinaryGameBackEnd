from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta

from db import get_db
import schemas
from models.models import User, Solve, DailyPuzzle
from auth.security import get_current_user
from routers.rankings import calculate_daily_ranking

router = APIRouter()


@router.get("/daily", response_model=list[schemas.CalendarDay])
def get_daily_calendar(
    db: Session = Depends(get_db),  # current_user: User = Depends(get_current_user)
    days: int = 30
):
    """
    Zwraca kalendarz aktywnosci uzytkownika:
    dni uczestnictwa + medal (1/2/3) jesli wystapil.
    """
    # DISABLED FOR PRESENTATION - use first user
    current_user = db.query(User).first()
    if not current_user:
        return []
    
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=days)
    
    calendar = []
    current_date = start_date
    
    while current_date <= today:
        # Check if there's a daily puzzle for this date
        daily_puzzle = db.query(DailyPuzzle).filter(
            DailyPuzzle.date == current_date
        ).first()
        
        if daily_puzzle:
            # Check if user solved it
            solve = db.query(Solve).filter(
                and_(
                    Solve.user_id == current_user.id,
                    Solve.puzzle_id == daily_puzzle.puzzle_id,
                    Solve.completed == True
                )
            ).first()
            
            medal = None
            if solve:
                # Calculate ranking to determine medal
                rankings = calculate_daily_ranking(current_date, db)
                user_ranking = next(
                    (r for r in rankings if r["user_id"] == str(current_user.id)),
                    None
                )
                
                if user_ranking:
                    rank = user_ranking["rank"]
                    if rank == 1:
                        medal = "gold"
                    elif rank == 2:
                        medal = "silver"
                    elif rank == 3:
                        medal = "bronze"
            
            calendar.append({
                "date": current_date,
                "participated": solve is not None,
                "medal": medal
            })
        
        current_date += timedelta(days=1)
    
    return calendar
