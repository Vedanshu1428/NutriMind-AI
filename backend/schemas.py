from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    age: int = Field(gt=0, lt=120)
    weight: float = Field(gt=0)
    height: float = Field(gt=0)
    goal: str
    diet_preference: str
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notification_opt_in: bool = False


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    id: int
    email: EmailStr
    age: int
    weight: float
    height: float
    goal: str
    diet_preference: str
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notification_opt_in: bool = False

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(TokenResponse):
    user: UserProfile


class FoodLogCreate(BaseModel):
    food_name: str = Field(min_length=1)
    quantity: float = Field(gt=0)
    consumed_at: Optional[datetime] = None


class FoodLogResponse(BaseModel):
    id: int
    food_name: str
    quantity: float
    consumed_at: datetime
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fats: float

    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    suggestions: List[str]
    nudges: List[str]
    habit_insights: List[str]
    health_score: int


class DailySummaryResponse(BaseModel):
    date: str
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fats: float
    calorie_goal: int
    remaining_calories: float
    logs: List[FoodLogResponse]
    recommendations: List[str]
    nudges: List[str]
    habit_insights: List[str]
    health_score: int


class AIRecommendationRequest(BaseModel):
    daily_food_log: Optional[List[FoodLogResponse]] = None


class AIRecommendationResponse(BaseModel):
    advice: str


class ScanFoodResponse(BaseModel):
    log: FoodLogResponse
    detected_food: str
    matched_food: str
    estimated_calories: float
    confidence: str


class HabitInsightsResponse(BaseModel):
    patterns: List[str]
    suggestions: List[str]


class HealthScoreResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    color: str
    calorie_goal_met: bool


class LocationPreferenceUpdate(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notification_opt_in: Optional[bool] = None


class DietPlanMeal(BaseModel):
    name: str
    calories: int
    protein_focus: str


class DietPlanDay(BaseModel):
    day: str
    breakfast: DietPlanMeal
    lunch: DietPlanMeal
    dinner: DietPlanMeal
    snack: DietPlanMeal
    daily_target_calories: int
    note: str


class WeeklyDietPlanResponse(BaseModel):
    week_start: datetime
    calorie_target: int
    focus: str
    generated_at: datetime
    days: List[DietPlanDay]


class RestaurantSuggestion(BaseModel):
    name: str
    cuisine: str
    address: str
    distance_km: float
    why_it_matches: str
    top_picks: List[str]


class RestaurantSuggestionResponse(BaseModel):
    resolved_location: str
    suggestions: List[RestaurantSuggestion]
    cached: bool = False


class NotificationItem(BaseModel):
    id: int
    title: str
    message: str
    channel: str
    notification_type: str
    scheduled_for: datetime
    sent_at: Optional[datetime] = None
    is_read: bool

    model_config = ConfigDict(from_attributes=True)


class NotificationFeedResponse(BaseModel):
    enabled: bool
    notifications: List[NotificationItem]


class DailyTrendPoint(BaseModel):
    date: str
    calories: float
    protein: float
    health_score: int


class WeeklyAnalyticsResponse(BaseModel):
    range_start: str
    range_end: str
    avg_calories: float
    avg_protein: float
    avg_health_score: float
    consistency_score: int
    streak_days: int
    calorie_goal: int
    daily_trends: List[DailyTrendPoint]
