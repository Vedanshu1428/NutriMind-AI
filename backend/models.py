from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    goal = Column(String, nullable=False)
    diet_preference = Column(String, nullable=False)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    notification_opt_in = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    food_logs = relationship("FoodLog", back_populates="user", cascade="all, delete-orphan")
    weekly_diet_plans = relationship("WeeklyDietPlan", back_populates="user", cascade="all, delete-orphan")
    notification_events = relationship("NotificationEvent", back_populates="user", cascade="all, delete-orphan")


class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    calories = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)
    healthier_alternative = Column(String, nullable=True)

    food_logs = relationship("FoodLog", back_populates="food_item")


class FoodLog(Base):
    __tablename__ = "food_logs"
    __table_args__ = (
        Index("ix_food_logs_user_consumed_at", "user_id", "consumed_at"),
        Index("ix_food_logs_user_created_at", "user_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    food_name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    consumed_at = Column(DateTime, nullable=False, index=True)
    total_calories = Column(Float, nullable=False)
    total_protein = Column(Float, nullable=False)
    total_carbs = Column(Float, nullable=False)
    total_fats = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="food_logs")
    food_item = relationship("FoodItem", back_populates="food_logs")


class WeeklyDietPlan(Base):
    __tablename__ = "weekly_diet_plans"
    __table_args__ = (Index("ix_weekly_diet_plans_user_week_start", "user_id", "week_start", unique=True),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    week_start = Column(DateTime, nullable=False)
    calorie_target = Column(Integer, nullable=False)
    focus = Column(String, nullable=False)
    plan_payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="weekly_diet_plans")


class NotificationEvent(Base):
    __tablename__ = "notification_events"
    __table_args__ = (
        Index("ix_notification_events_user_scheduled", "user_id", "scheduled_for"),
        Index("ix_notification_events_user_read", "user_id", "is_read"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    channel = Column(String, nullable=False, default="browser")
    notification_type = Column(String, nullable=False, default="habit_nudge")
    scheduled_for = Column(DateTime, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="notification_events")
