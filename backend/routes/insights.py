from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import HabitInsightsResponse, HealthScoreResponse
from security import get_current_user
from service_layer.log_service import fetch_logs_for_day, fetch_logs_for_range
from services import build_habit_insights, calculate_health_score


router = APIRouter()

@router.get("/habit-insights", response_model=HabitInsightsResponse)
def habit_insights(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = fetch_logs_for_range(db, current_user.id, datetime.utcnow() - timedelta(days=7), datetime.utcnow() + timedelta(minutes=1))
    patterns, suggestions = build_habit_insights(logs)
    return HabitInsightsResponse(patterns=patterns, suggestions=suggestions)


@router.get("/health-score", response_model=HealthScoreResponse)
def health_score(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = datetime.utcnow().date()
    today_logs = fetch_logs_for_day(db, current_user.id, today)
    score, color, calorie_goal_met = calculate_health_score(current_user, today_logs)
    return HealthScoreResponse(score=score, color=color, calorie_goal_met=calorie_goal_met)
