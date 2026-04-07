from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import (
    LocationPreferenceUpdate,
    NotificationFeedResponse,
    NotificationItem,
    RestaurantSuggestionResponse,
    UserProfile,
    WeeklyAnalyticsResponse,
    WeeklyDietPlanResponse,
)
from security import get_current_user
from service_layer import analytics_cache, diet_plan_cache, notification_cache, restaurant_cache
from service_layer.analytics_service import get_weekly_analytics
from service_layer.diet_service import get_weekly_diet_plan
from service_layer.notification_service import get_notification_feed, mark_notification_as_read
from service_layer.restaurant_service import get_restaurant_suggestions


router = APIRouter()


def invalidate_user_caches(user_id: int) -> None:
    prefix = f"user:{user_id}:"
    diet_plan_cache.invalidate_prefix(prefix)
    restaurant_cache.invalidate_prefix(prefix)
    analytics_cache.invalidate_prefix(prefix)
    notification_cache.invalidate_prefix(prefix)


@router.get("/weekly-diet-plan", response_model=WeeklyDietPlanResponse)
def weekly_diet_plan(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan, _ = get_weekly_diet_plan(db, current_user)
    return plan


@router.get("/restaurants/suggestions", response_model=RestaurantSuggestionResponse)
def restaurant_suggestions(
    latitude: float | None = Query(default=None),
    longitude: float | None = Query(default=None),
    city: str | None = Query(default=None),
    country: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    return get_restaurant_suggestions(current_user, latitude=latitude, longitude=longitude, city=city, country=country)


@router.get("/notifications/feed", response_model=NotificationFeedResponse)
def notification_feed(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_notification_feed(db, current_user)


@router.post("/notifications/{notification_id}/read", response_model=NotificationItem)
def read_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = mark_notification_as_read(db, current_user.id, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationItem.model_validate(notification)


@router.get("/analytics/weekly-trends", response_model=WeeklyAnalyticsResponse)
def weekly_trends(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_weekly_analytics(db, current_user)


@router.patch("/profile/preferences", response_model=UserProfile)
def update_preferences(
    payload: LocationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for field in ["city", "country", "latitude", "longitude", "notification_opt_in"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(current_user, field, value)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    invalidate_user_caches(current_user.id)
    return UserProfile.model_validate(current_user)
