from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models import FoodLog, NotificationEvent, User
from schemas import NotificationFeedResponse
from service_layer.cache import notification_cache
from service_layer.log_service import fetch_logs_for_range
from services import build_habit_insights


def _build_notification_candidates(user: User, logs: list[FoodLog]) -> list[tuple[str, str]]:
    patterns, suggestions = build_habit_insights(logs)
    candidates: list[tuple[str, str]] = []

    if not logs:
        candidates.append(("Start your streak", "Log your first meal today so the coach can tailor your nudges."))

    for pattern in patterns[:2]:
        candidates.append(("Habit nudge", pattern))
    for suggestion in suggestions[:2]:
        candidates.append(("Coach tip", suggestion))

    if user.goal in {"weight_loss", "lose"}:
        candidates.append(("Momentum check", "Keep one high-protein, lower-calorie meal ready for your busiest part of the day."))

    deduped: list[tuple[str, str]] = []
    seen = set()
    for title, message in candidates:
        key = f"{title}:{message}"
        if key not in seen:
            seen.add(key)
            deduped.append((title, message))
    return deduped[:3]


def sync_notification_queue(db: Session, user: User) -> None:
    if not user.notification_opt_in:
        return

    now = datetime.utcnow()
    existing = (
        db.query(NotificationEvent)
        .filter(
            NotificationEvent.user_id == user.id,
            NotificationEvent.scheduled_for >= now - timedelta(hours=4),
        )
        .all()
    )
    if existing:
        return

    recent_logs = fetch_logs_for_range(db, user.id, now - timedelta(days=7), now + timedelta(minutes=1))
    schedule_time = now + timedelta(minutes=1)
    for offset, (title, message) in enumerate(_build_notification_candidates(user, recent_logs)):
        db.add(
            NotificationEvent(
                user_id=user.id,
                title=title,
                message=message,
                scheduled_for=schedule_time + timedelta(minutes=offset * 45),
            )
        )
    db.commit()


def get_notification_feed(db: Session, user: User) -> NotificationFeedResponse:
    sync_notification_queue(db, user)
    cache_key = f"user:{user.id}:notifications"
    cached = notification_cache.get(cache_key)
    if cached:
        return NotificationFeedResponse.model_validate(cached)

    notifications = (
        db.query(NotificationEvent)
        .filter(NotificationEvent.user_id == user.id)
        .order_by(NotificationEvent.scheduled_for.asc())
        .limit(10)
        .all()
    )
    payload = {
        "enabled": user.notification_opt_in,
        "notifications": notifications,
    }
    notification_cache.set(cache_key, payload)
    return NotificationFeedResponse.model_validate(payload)


def mark_notification_as_read(db: Session, user_id: int, notification_id: int) -> NotificationEvent | None:
    notification = (
        db.query(NotificationEvent)
        .filter(NotificationEvent.id == notification_id, NotificationEvent.user_id == user_id)
        .first()
    )
    if not notification:
        return None
    notification.is_read = True
    if notification.sent_at is None:
        notification.sent_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)
    notification_cache.invalidate(f"user:{user_id}:notifications")
    return notification
