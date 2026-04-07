from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models import FoodLog


def get_day_window(target_day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(target_day, time.min)
    end = start + timedelta(days=1)
    return start, end


def fetch_logs_for_day(db: Session, user_id: int, target_day: date) -> list[FoodLog]:
    start, end = get_day_window(target_day)
    return (
        db.query(FoodLog)
        .options(joinedload(FoodLog.food_item))
        .filter(FoodLog.user_id == user_id, FoodLog.consumed_at >= start, FoodLog.consumed_at < end)
        .order_by(FoodLog.consumed_at.desc())
        .all()
    )


def fetch_logs_for_range(db: Session, user_id: int, start_at: datetime, end_at: datetime) -> list[FoodLog]:
    return (
        db.query(FoodLog)
        .options(joinedload(FoodLog.food_item))
        .filter(FoodLog.user_id == user_id, FoodLog.consumed_at >= start_at, FoodLog.consumed_at < end_at)
        .order_by(FoodLog.consumed_at.desc())
        .all()
    )


def fetch_daily_macro_totals(db: Session, user_id: int, days: int = 7) -> list[dict]:
    start_at = datetime.combine(datetime.utcnow().date() - timedelta(days=days - 1), time.min)
    rows = (
        db.query(
            func.date(FoodLog.consumed_at).label("day"),
            func.sum(FoodLog.total_calories).label("calories"),
            func.sum(FoodLog.total_protein).label("protein"),
            func.sum(FoodLog.total_carbs).label("carbs"),
            func.sum(FoodLog.total_fats).label("fats"),
        )
        .filter(FoodLog.user_id == user_id, FoodLog.consumed_at >= start_at)
        .group_by(func.date(FoodLog.consumed_at))
        .order_by(func.date(FoodLog.consumed_at))
        .all()
    )
    return [
        {
            "date": str(row.day),
            "calories": round(float(row.calories or 0), 2),
            "protein": round(float(row.protein or 0), 2),
            "carbs": round(float(row.carbs or 0), 2),
            "fats": round(float(row.fats or 0), 2),
        }
        for row in rows
    ]
