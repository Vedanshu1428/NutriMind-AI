import base64
import json
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from openai import OpenAI
from sqlalchemy.orm import Session

from database import get_db
from models import FoodItem, FoodLog, User
from schemas import DailySummaryResponse, FoodLogCreate, FoodLogResponse, ScanFoodResponse
from security import get_current_user
from service_layer import analytics_cache, diet_plan_cache, notification_cache, restaurant_cache
from service_layer.log_service import fetch_logs_for_day, fetch_logs_for_range
from services import build_food_recommendations, find_matching_food_item, get_calorie_goal


router = APIRouter()


def invalidate_user_caches(user_id: int) -> None:
    prefix = f"user:{user_id}:"
    diet_plan_cache.invalidate_prefix(prefix)
    restaurant_cache.invalidate_prefix(prefix)
    analytics_cache.invalidate_prefix(prefix)
    notification_cache.invalidate_prefix(prefix)


def create_food_log(db: Session, current_user: User, food_item: FoodItem, quantity: float, consumed_at: datetime) -> FoodLog:
    log = FoodLog(
        user_id=current_user.id,
        food_item_id=food_item.id,
        food_name=food_item.name,
        quantity=quantity,
        consumed_at=consumed_at,
        total_calories=food_item.calories * quantity,
        total_protein=food_item.protein * quantity,
        total_carbs=food_item.carbs * quantity,
        total_fats=food_item.fats * quantity,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    invalidate_user_caches(current_user.id)
    return log


@router.post("/log-food", response_model=FoodLogResponse, status_code=status.HTTP_201_CREATED)
def log_food(
    payload: FoodLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    food_item = db.query(FoodItem).filter(FoodItem.name.ilike(payload.food_name.strip())).first()
    if not food_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found in database. Try one of the seeded foods.",
        )

    consumed_at = payload.consumed_at or datetime.utcnow()
    return create_food_log(db, current_user, food_item, payload.quantity, consumed_at)


@router.post("/scan-food", response_model=ScanFoodResponse, status_code=status.HTTP_201_CREATED)
async def scan_food(
    image: UploadFile = File(...),
    quantity: float = Form(1.0),
    consumed_at: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0.")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    mime_type = image.content_type or "image/jpeg"
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    available_foods = db.query(FoodItem).order_by(FoodItem.name.asc()).all()

    client = OpenAI(api_key=api_key)
    try:
        response = client.responses.create(
            model=os.getenv("OPENAI_VISION_MODEL", os.getenv("OPENAI_MODEL", "gpt-4.1-mini")),
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Identify the main food shown in the image. Respond with the closest food name from the provided list when possible. "
                                "Estimate calories for one serving and return a confidence label of low, medium, or high."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"Allowed food matches: {', '.join(item.name for item in available_foods)}",
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:{mime_type};base64,{encoded_image}",
                        },
                    ],
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "food_scan",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detected_food": {"type": "string"},
                            "matched_food": {"type": "string"},
                            "estimated_calories": {"type": "number"},
                            "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                        },
                        "required": ["detected_food", "matched_food", "estimated_calories", "confidence"],
                        "additionalProperties": False,
                    },
                }
            },
        )
        parsed = json.loads(response.output_text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Food scan failed: {exc}") from exc

    detected_food = parsed.get("detected_food", "").strip()
    matched_food_name = parsed.get("matched_food", detected_food).strip()
    confidence = parsed.get("confidence", "medium")
    matched_food = find_matching_food_item(matched_food_name or detected_food, available_foods)

    if not matched_food:
        raise HTTPException(
            status_code=404,
            detail="The food was detected, but it could not be matched to the current food database.",
        )

    consumed_at_value = datetime.fromisoformat(consumed_at.replace("Z", "+00:00")) if consumed_at else datetime.utcnow()
    log = create_food_log(db, current_user, matched_food, quantity, consumed_at_value)

    return ScanFoodResponse(
        log=FoodLogResponse.model_validate(log),
        detected_food=detected_food or matched_food.name,
        matched_food=matched_food.name,
        estimated_calories=round(matched_food.calories * quantity, 2),
        confidence=confidence,
    )


@router.get("/daily-summary", response_model=DailySummaryResponse)
def daily_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = datetime.utcnow().date()
    today_logs = fetch_logs_for_day(db, current_user.id, today)
    history_logs = fetch_logs_for_range(
        db,
        current_user.id,
        datetime.combine(today, datetime.min.time()) - timedelta(days=7),
        datetime.combine(today, datetime.min.time()),
    )

    total_calories = sum(log.total_calories for log in today_logs)
    total_protein = sum(log.total_protein for log in today_logs)
    total_carbs = sum(log.total_carbs for log in today_logs)
    total_fats = sum(log.total_fats for log in today_logs)
    calorie_goal = get_calorie_goal(current_user)
    recommendations, nudges, habit_insights, health_score = build_food_recommendations(current_user, today_logs, history_logs)

    return DailySummaryResponse(
        date=str(today),
        total_calories=round(total_calories, 2),
        total_protein=round(total_protein, 2),
        total_carbs=round(total_carbs, 2),
        total_fats=round(total_fats, 2),
        calorie_goal=calorie_goal,
        remaining_calories=round(calorie_goal - total_calories, 2),
        logs=[FoodLogResponse.model_validate(log) for log in today_logs],
        recommendations=recommendations,
        nudges=nudges,
        habit_insights=habit_insights,
        health_score=health_score,
    )
