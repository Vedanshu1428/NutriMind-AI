from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models import User
from schemas import WeeklyAnalyticsResponse
from service_layer.cache import analytics_cache
from service_layer.log_service import fetch_daily_macro_totals, fetch_logs_for_range
from services import get_calorie_goal, get_daily_health_score, group_logs_by_date


def calculate_streak(dates_with_logs: set[str]) -> int:
    streak = 0
    current = datetime.utcnow().date()
    while current.isoformat() in dates_with_logs:
        streak += 1
        current -= timedelta(days=1)
    return streak


def get_weekly_analytics(db: Session, user: User) -> WeeklyAnalyticsResponse:
    cache_key = f"user:{user.id}:analytics"
    cached = analytics_cache.get(cache_key)
    if cached:
        return WeeklyAnalyticsResponse.model_validate(cached)

    daily_totals = fetch_daily_macro_totals(db, user.id, days=7)
    start_at = datetime.combine(datetime.utcnow().date() - timedelta(days=6), datetime.min.time())
    end_at = datetime.utcnow() + timedelta(minutes=1)
    logs = fetch_logs_for_range(db, user.id, start_at, end_at)
    grouped_logs = group_logs_by_date(logs)
    health_scores_by_day = {day.isoformat(): get_daily_health_score(day_logs) for day, day_logs in grouped_logs.items()}

    daily_trends = []
    for offset in range(7):
        day = (datetime.utcnow().date() - timedelta(days=6 - offset)).isoformat()
        totals = next((row for row in daily_totals if row["date"] == day), None)
        daily_trends.append(
            {
                "date": day,
                "calories": totals["calories"] if totals else 0,
                "protein": totals["protein"] if totals else 0,
                "health_score": health_scores_by_day.get(day, 70 if totals else 0),
            }
        )

    logged_days = [point for point in daily_trends if point["calories"] > 0]
    avg_calories = round(sum(point["calories"] for point in logged_days) / max(1, len(logged_days)), 2)
    avg_protein = round(sum(point["protein"] for point in logged_days) / max(1, len(logged_days)), 2)
    avg_health_score = round(sum(point["health_score"] for point in logged_days) / max(1, len(logged_days)), 1)
    calorie_goal = get_calorie_goal(user)
    on_target_days = sum(1 for point in logged_days if point["calories"] <= calorie_goal)
    consistency_score = round(((len(logged_days) * 0.55) + (on_target_days * 0.45)) / 7 * 100)

    payload = {
        "range_start": daily_trends[0]["date"],
        "range_end": daily_trends[-1]["date"],
        "avg_calories": avg_calories,
        "avg_protein": avg_protein,
        "avg_health_score": avg_health_score,
        "consistency_score": max(0, min(100, consistency_score)),
        "streak_days": calculate_streak({point["date"] for point in logged_days}),
        "calorie_goal": calorie_goal,
        "daily_trends": daily_trends,
    }
    analytics_cache.set(cache_key, payload)
    return WeeklyAnalyticsResponse.model_validate(payload)
