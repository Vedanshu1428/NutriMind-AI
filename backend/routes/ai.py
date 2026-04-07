import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import FoodLog, User
from schemas import AIRecommendationRequest, AIRecommendationResponse
from security import get_current_user
from services import filter_logs_for_day, get_calorie_goal, get_daily_health_score, get_recent_history


router = APIRouter()


@router.post("/ai-recommend", response_model=AIRecommendationResponse)
def ai_recommend(
    payload: AIRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    today = datetime.utcnow().date()
    logs = (
        db.query(FoodLog)
        .options(joinedload(FoodLog.food_item))
        .filter(FoodLog.user_id == current_user.id)
        .order_by(FoodLog.consumed_at.asc())
        .all()
    )
    today_logs = payload.daily_food_log or [
        {
            "food_name": log.food_name,
            "quantity": log.quantity,
            "consumed_at": log.consumed_at.isoformat(),
            "total_calories": log.total_calories,
            "total_protein": log.total_protein,
            "total_carbs": log.total_carbs,
            "total_fats": log.total_fats,
        }
        for log in filter_logs_for_day(logs, today)
    ]
    recent_history = get_recent_history(logs, today)
    common_recent_foods = {}
    for log in recent_history:
        common_recent_foods[log.food_name] = common_recent_foods.get(log.food_name, 0) + 1

    client = OpenAI(api_key=api_key)
    calorie_goal = get_calorie_goal(current_user)
    health_score = get_daily_health_score(filter_logs_for_day(logs, today))

    try:
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a supportive nutrition coach. Give practical, personalized, non-medical advice based "
                        "on the user's goal, diet preference, and food log. Keep it concise, encouraging, and specific."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"User goal: {current_user.goal}\n"
                        f"Diet preference: {current_user.diet_preference}\n"
                        f"Calorie goal: {calorie_goal}\n"
                        f"Today's health score: {health_score}/100\n"
                        f"Recent habit summary: {common_recent_foods}\n"
                        f"Today's log: {today_logs}\n"
                        "Provide a short summary, one behavior insight tied to recent habits, and two actionable suggestions."
                    ),
                },
            ],
        )
        advice = response.output_text
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI recommendation failed: {exc}") from exc

    return AIRecommendationResponse(advice=advice)
