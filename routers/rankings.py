from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime

from db import get_db
import schemas
from models.models import DailyRanking, DailyPuzzle, Solve, User

router = APIRouter()


def calculate_daily_ranking(date_obj, db: Session):
    """
    Kalkuluje ranking dla danej daty.
    Ranking liczony po: 
    1: kto mial najmniej bledow
    2: kto uzyl najmniej hintow
    3: kto wykonal najmniej ruchow
    4: najmniejszy czas
    """
    # Get daily puzzle for this date
    daily_puzzle = db.query(DailyPuzzle).filter(DailyPuzzle.date == date_obj).first()
    if not daily_puzzle:
        return []
    
    # Get all completed solves for this puzzle
    solves = db.query(Solve).filter(
        and_(
            Solve.puzzle_id == daily_puzzle.puzzle_id,
            Solve.completed == True
        )
    ).all()
    
    # Sort by ranking criteria
    sorted_solves = sorted(
        solves,
        key=lambda s: (s.mistakes, s.hints_used, s.time_seconds or 999999)
    )
    
    # Calculate scores and ranks
    rankings = []
    for rank, solve in enumerate(sorted_solves, start=1):
        # Score formula (higher is better)
        score = 10000 - (solve.mistakes * 100) - (solve.hints_used * 50) - (solve.time_seconds or 0)
        rankings.append({
            "rank": rank,
            "user_id": solve.user_id,
            "score": max(0, score),
            "mistakes": solve.mistakes,
            "hints_used": solve.hints_used,
            "time_seconds": solve.time_seconds
        })
    
    return rankings


@router.get("/daily/{date}", response_model=list[schemas.DailyRankingPublic])
def get_daily_ranking(date: str, db: Session = Depends(get_db)):
    """Zwraca pelny ranking daily puzzle dla danej daty."""
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    rankings = calculate_daily_ranking(date_obj, db)
    
    # Enrich with user data
    result = []
    for r in rankings:
        user = db.query(User).filter(User.id == r["user_id"]).first()
        result.append({
            "rank": r["rank"],
            "user_id": r["user_id"],
            "user_nick": user.nick if user else "Unknown",
            "score": r["score"],
            "mistakes": r["mistakes"],
            "hints_used": r["hints_used"],
            "time_seconds": r["time_seconds"]
        })
    
    return result


@router.get("/daily/{date}/top", response_model=list[schemas.DailyRankingPublic])
def get_daily_top(date: str, limit: int = 10, db: Session = Depends(get_db)):
    """Zwraca TOP N (np. 10) wynikow dla daily puzzle."""
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    rankings = calculate_daily_ranking(date_obj, db)
    top_rankings = rankings[:limit]
    
    # Enrich with user data
    result = []
    for r in top_rankings:
        user = db.query(User).filter(User.id == r["user_id"]).first()
        result.append({
            "rank": r["rank"],
            "user_id": r["user_id"],
            "user_nick": user.nick if user else "Unknown",
            "score": r["score"],
            "mistakes": r["mistakes"],
            "hints_used": r["hints_used"],
            "time_seconds": r["time_seconds"]
        })
    
    return result


@router.get("/user/{user_id}", response_model=list[schemas.UserRankingHistory])
def get_user_rankings(user_id: str, db: Session = Depends(get_db)):
    """Zwraca historie wynikow rankingowych danego uzytkownika."""
    # Get all daily puzzles the user completed
    solves = db.query(Solve).filter(
        and_(
            Solve.user_id == user_id,
            Solve.completed == True
        )
    ).all()
    
    history = []
    for solve in solves:
        # Find the daily puzzle for this solve
        daily_puzzle = db.query(DailyPuzzle).filter(
            DailyPuzzle.puzzle_id == solve.puzzle_id
        ).first()
        
        if daily_puzzle:
            # Calculate ranking for that day
            rankings = calculate_daily_ranking(daily_puzzle.date, db)
            user_ranking = next((r for r in rankings if r["user_id"] == user_id), None)
            
            if user_ranking:
                history.append({
                    "date": daily_puzzle.date,
                    "rank": user_ranking["rank"],
                    "score": user_ranking["score"],
                    "total_participants": len(rankings)
                })
    
    # Sort by date descending
    history.sort(key=lambda x: x["date"], reverse=True)
    return history
