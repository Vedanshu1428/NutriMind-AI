from __future__ import annotations

from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session

from models import User, WeeklyDietPlan
from schemas import WeeklyDietPlanResponse
from service_layer.cache import diet_plan_cache
from service_layer.log_service import fetch_logs_for_range
from services import get_calorie_goal


MEAL_LIBRARY = {
    "balanced": {
        "breakfast": [("Greek Yogurt Parfait", 340, "protein + probiotics"), ("Oatmeal With Berries", 320, "slow carbs")],
        "lunch": [("Brown Rice Power Bowl", 540, "fiber + steady energy"), ("Grilled Chicken Salad", 480, "lean protein")],
        "dinner": [("Salmon Veggie Plate", 590, "omega-3 recovery"), ("Chicken Stir Fry", 560, "balanced macros")],
        "snack": [("Fruit Smoothie", 180, "micronutrient boost"), ("Greek Yogurt Cup", 140, "high protein")],
    },
    "vegetarian": {
        "breakfast": [("Overnight Oats", 310, "fiber + satiety"), ("Greek Yogurt Parfait", 330, "protein + probiotics")],
        "lunch": [("Chickpea Grain Bowl", 510, "plant protein"), ("Paneer Salad Bowl", 470, "protein + calcium")],
        "dinner": [("Tofu Stir Fry", 540, "lean plant protein"), ("Lentil Brown Rice Plate", 560, "steady energy")],
        "snack": [("Fruit Smoothie", 170, "vitamin dense"), ("Roasted Chickpeas", 160, "crunchy protein")],
    },
    "high_protein": {
        "breakfast": [("Egg Omelette + Toast", 360, "high protein"), ("Greek Yogurt Protein Bowl", 340, "muscle support")],
        "lunch": [("Grilled Chicken Bowl", 520, "lean protein"), ("Turkey Veggie Wrap", 500, "recovery fuel")],
        "dinner": [("Chicken Stir Fry", 570, "lean dinner protein"), ("Salmon Veggie Plate", 600, "protein + fats")],
        "snack": [("Greek Yogurt Cup", 140, "protein top-up"), ("Protein Smoothie", 210, "recovery")],
    },
    "low_carb": {
        "breakfast": [("Egg Omelette", 300, "protein-first"), ("Greek Yogurt Bowl", 280, "lower carb")],
        "lunch": [("Chicken Caesar Salad", 450, "protein + greens"), ("Tofu Salad Bowl", 430, "light lunch")],
        "dinner": [("Salmon Veggie Plate", 580, "healthy fats"), ("Grilled Chicken Greens", 500, "lean low-carb")],
        "snack": [("Greek Yogurt Cup", 120, "protein support"), ("Handful of Nuts", 170, "healthy fats")],
    },
}

DAY_NOTES = [
    "Front-load protein early to reduce late-night cravings.",
    "Keep lunch fiber-rich to stabilize afternoon energy.",
    "Hydrate before your afternoon snack to avoid mindless eating.",
    "Make dinner lighter if your activity level is lower today.",
    "Aim for one extra vegetable serving to boost micronutrients.",
    "Use your snack as a protein anchor instead of a sugar spike.",
    "Prep tomorrow's first meal tonight to protect consistency.",
]


def get_week_start(reference: datetime | None = None) -> datetime:
    reference = reference or datetime.utcnow()
    start = datetime.combine((reference - timedelta(days=reference.weekday())).date(), time.min)
    return start


def build_plan_payload(user: User, recent_avg_calories: float | None) -> dict:
    preference = user.diet_preference if user.diet_preference in MEAL_LIBRARY else "balanced"
    library = MEAL_LIBRARY[preference]
    calorie_target = get_calorie_goal(user)
    adjustment = -100 if recent_avg_calories and recent_avg_calories > calorie_target else 100 if recent_avg_calories and recent_avg_calories < calorie_target * 0.8 else 0
    effective_target = calorie_target + adjustment
    days = []

    for index, day_name in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
        breakfast = library["breakfast"][index % len(library["breakfast"])]
        lunch = library["lunch"][index % len(library["lunch"])]
        dinner = library["dinner"][index % len(library["dinner"])]
        snack = library["snack"][index % len(library["snack"])]
        days.append(
            {
                "day": day_name,
                "breakfast": {"name": breakfast[0], "calories": breakfast[1], "protein_focus": breakfast[2]},
                "lunch": {"name": lunch[0], "calories": lunch[1], "protein_focus": lunch[2]},
                "dinner": {"name": dinner[0], "calories": dinner[1], "protein_focus": dinner[2]},
                "snack": {"name": snack[0], "calories": snack[1], "protein_focus": snack[2]},
                "daily_target_calories": effective_target,
                "note": DAY_NOTES[index],
            }
        )

    return {"calorie_target": effective_target, "focus": preference.replace("_", " "), "days": days}


def get_weekly_diet_plan(db: Session, user: User) -> tuple[WeeklyDietPlanResponse, bool]:
    week_start = get_week_start()
    cache_key = f"user:{user.id}:week:{week_start.date().isoformat()}"
    cached = diet_plan_cache.get(cache_key)
    if cached:
        return WeeklyDietPlanResponse.model_validate(cached), True

    plan = db.query(WeeklyDietPlan).filter(WeeklyDietPlan.user_id == user.id, WeeklyDietPlan.week_start == week_start).first()

    if not plan:
        recent_logs = fetch_logs_for_range(db, user.id, week_start - timedelta(days=7), week_start)
        recent_avg_calories = None
        if recent_logs:
            recent_avg_calories = sum(log.total_calories for log in recent_logs) / max(1, len(recent_logs))
        payload = build_plan_payload(user, recent_avg_calories)
        plan = WeeklyDietPlan(
            user_id=user.id,
            week_start=week_start,
            calorie_target=payload["calorie_target"],
            focus=payload["focus"],
            plan_payload=payload,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

    response_payload = {
        "week_start": plan.week_start,
        "calorie_target": plan.calorie_target,
        "focus": plan.focus,
        "generated_at": plan.updated_at,
        "days": plan.plan_payload["days"],
    }
    diet_plan_cache.set(cache_key, response_payload)
    return WeeklyDietPlanResponse.model_validate(response_payload), False
