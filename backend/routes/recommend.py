from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import RecommendationResponse
from security import get_current_user
from service_layer.log_service import fetch_logs_for_day, fetch_logs_for_range
from services import build_food_recommendations


router = APIRouter()


@router.get("/recommendations", response_model=RecommendationResponse)
def recommendations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = datetime.utcnow().date()
    today_logs = fetch_logs_for_day(db, current_user.id, today)
    history_logs = fetch_logs_for_range(
        db,
        current_user.id,
        datetime.combine(today, datetime.min.time()) - timedelta(days=7),
        datetime.combine(today, datetime.min.time()),
    )
    suggestions, nudges, habit_insights, health_score = build_food_recommendations(current_user, today_logs, history_logs)
    return RecommendationResponse(
        suggestions=suggestions,
        nudges=nudges,
        habit_insights=habit_insights,
        health_score=health_score,
    )
