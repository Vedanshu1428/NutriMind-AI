from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from typing import Iterable, List
import difflib

from models import FoodLog, FoodItem, User


GOAL_CALORIE_MAP = {
    "lose": 1800,
    "weight_loss": 1800,
    "gain": 2600,
    "weight_gain": 2600,
    "maintain": 2200,
    "maintenance": 2200,
}


def normalize_goal(goal: str) -> str:
    return goal.strip().lower().replace(" ", "_")


def get_calorie_goal(user: User) -> int:
    return GOAL_CALORIE_MAP.get(normalize_goal(user.goal), 2200)


def get_time_based_suggestion(consumed_at: datetime) -> str | None:
    current_time = consumed_at.time()
    if time(5, 0) <= current_time <= time(10, 59):
        return "Morning tip: prioritize high-protein options like eggs, Greek yogurt, or grilled chicken."
    if time(20, 0) <= current_time <= time(23, 59):
        return "Night tip: keep dinner lighter with lower-calorie, fiber-rich foods."
    return None


def get_food_health_score(food_item: FoodItem) -> int:
    if food_item.category == "healthy":
        return 88
    if food_item.category == "junk":
        return 32
    return 60


def get_log_health_score(log: FoodLog) -> int:
    score = get_food_health_score(log.food_item)
    if log.total_calories > 450:
        score -= 10
    if log.total_protein >= 20:
        score += 6
    if log.total_fats > 25:
        score -= 6
    return max(0, min(100, score))


def get_daily_health_score(logs: Iterable[FoodLog]) -> int:
    scored_logs = [get_log_health_score(log) for log in logs]
    if not scored_logs:
        return 75
    return round(sum(scored_logs) / len(scored_logs))


def find_matching_food_item(food_name: str, food_items: Iterable[FoodItem]) -> FoodItem | None:
    indexed_items = {item.name.lower(): item for item in food_items}
    normalized_name = food_name.strip().lower()
    if normalized_name in indexed_items:
        return indexed_items[normalized_name]

    matches = difflib.get_close_matches(normalized_name, indexed_items.keys(), n=1, cutoff=0.45)
    if matches:
        return indexed_items[matches[0]]
    return None


def get_recent_history(logs: Iterable[FoodLog], target_date: date, days: int = 7) -> list[FoodLog]:
    cutoff = target_date - timedelta(days=days)
    return [log for log in logs if cutoff <= log.consumed_at.date() < target_date]


def is_breakfast_time(consumed_at: datetime) -> bool:
    return time(5, 0) <= consumed_at.time() <= time(10, 59)


def is_night_time(consumed_at: datetime) -> bool:
    return time(20, 0) <= consumed_at.time() <= time(23, 59)


def group_logs_by_date(logs: Iterable[FoodLog]) -> dict[date, list[FoodLog]]:
    grouped_logs: dict[date, list[FoodLog]] = defaultdict(list)
    for log in logs:
        grouped_logs[log.consumed_at.date()].append(log)
    return dict(grouped_logs)


def get_recent_logs(logs: Iterable[FoodLog], days: int = 7) -> list[FoodLog]:
    # Recent windows keep habit feedback focused on current behavior.
    cutoff = datetime.utcnow().date() - timedelta(days=days - 1)
    return [log for log in logs if log.consumed_at.date() >= cutoff]


def build_habit_insights(logs: Iterable[FoodLog]) -> tuple[List[str], List[str]]:
    patterns: list[str] = []
    suggestions: list[str] = []
    recent_logs = get_recent_logs(logs)
    logs_by_date = group_logs_by_date(recent_logs)

    if not logs_by_date:
        return (
            ["Log a few meals to unlock your habit insights."],
            ["Start by tracking breakfast, lunch, dinner, and snacks for a few days."],
        )

    junk_heavy_days = 0
    repeated_unhealthy_behaviors = Counter()

    for day_logs in logs_by_date.values():
        junk_logs = [log for log in day_logs if log.food_item.category == "junk"]
        night_junk_logs = [log for log in junk_logs if is_night_time(log.consumed_at)]
        has_breakfast = any(is_breakfast_time(log.consumed_at) for log in day_logs)

        if len(junk_logs) > 2:
            junk_heavy_days += 1
            repeated_unhealthy_behaviors["high_junk_intake"] += 1

        if night_junk_logs:
            repeated_unhealthy_behaviors["night_junk"] += 1

        if not has_breakfast:
            repeated_unhealthy_behaviors["skip_breakfast"] += 1

    # This flags the day-level habit requested by the feature spec.
    if junk_heavy_days:
        patterns.append("You have days where you eat junk food more than twice.")
        suggestions.append("Plan one healthier swap ahead of time for your highest-risk meals.")

    if repeated_unhealthy_behaviors["night_junk"] >= 3:
        patterns.append("You tend to eat junk food at night.")
        suggestions.append("Try replacing late-night snacks with fruits.")

    if repeated_unhealthy_behaviors["skip_breakfast"] >= 3:
        patterns.append("You skip breakfast frequently.")
        suggestions.append("Eat a high-protein breakfast.")

    if repeated_unhealthy_behaviors["high_junk_intake"] >= 3:
        patterns.append("High junk-food intake has become a repeating pattern over the last few days.")
        suggestions.append("Keep convenient healthy meals ready so you are less likely to rely on junk food.")

    if not patterns:
        patterns.append("Your recent meal timing looks fairly steady.")
        suggestions.append("Keep logging meals consistently so the coach can spot meaningful trends early.")

    return list(dict.fromkeys(patterns)), list(dict.fromkeys(suggestions))


def get_health_score_color(score: int) -> str:
    if score >= 80:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


def calculate_health_score(user: User, logs: Iterable[FoodLog]) -> tuple[int, str, bool]:
    today_logs = list(logs)
    score = 50

    for log in today_logs:
        if log.food_item.category == "healthy":
            score += 10
        elif log.food_item.category == "junk":
            score -= 10

    total_calories = sum(log.total_calories for log in today_logs)
    calorie_goal = get_calorie_goal(user)
    calorie_goal_met = bool(today_logs) and total_calories <= calorie_goal
    if calorie_goal_met:
        score += 20

    bounded_score = max(0, min(100, score))
    return bounded_score, get_health_score_color(bounded_score), calorie_goal_met


def build_food_recommendations(
    user: User,
    today_logs: Iterable[FoodLog],
    history_logs: Iterable[FoodLog] | None = None,
) -> tuple[List[str], List[str], List[str], int]:
    suggestions: list[str] = []
    nudges: list[str] = []
    habit_insights: list[str] = []
    unhealthy_count = 0
    repeated_foods = Counter()
    history_logs = list(history_logs or [])
    today_logs = list(today_logs)
    history_foods = Counter(log.food_name.lower() for log in history_logs)

    for log in today_logs:
        repeated_foods[log.food_name.lower()] += 1
        food_item: FoodItem = log.food_item

        if food_item.category == "junk":
            unhealthy_count += 1
            if normalize_goal(user.goal) in {"lose", "weight_loss"} and food_item.healthier_alternative:
                suggestions.append(
                    f"{log.food_name} is working against your weight-loss goal. Try {food_item.healthier_alternative} instead."
                )

        time_hint = get_time_based_suggestion(log.consumed_at)
        if time_hint:
            suggestions.append(time_hint)

    for food_name, count in repeated_foods.items():
        if count >= 2:
            suggestions.append(
                f"You logged {food_name.title()} {count} times today. Consider rotating in more whole-food choices for better balance."
            )
        if history_foods[food_name] >= 3:
            habit_insights.append(
                f"{food_name.title()} has shown up often in your recent history. Mixing in alternative meals can improve variety and micronutrient coverage."
            )

    if unhealthy_count >= 3:
        nudges.append(f"You ate junk food {unhealthy_count} times today. Try swapping one meal for a healthier option.")

    total_calories = sum(log.total_calories for log in today_logs)
    calorie_goal = get_calorie_goal(user)
    if calorie_goal - 250 <= total_calories <= calorie_goal:
        nudges.append("You're close to your calorie goal. Keep the rest of the day balanced and portion-aware.")
    if total_calories > calorie_goal:
        nudges.append("You've crossed your calorie goal for today. Choose lighter meals or snacks next.")

    if history_logs:
        avg_recent_calories = sum(log.total_calories for log in history_logs) / max(1, len(history_logs))
        if avg_recent_calories > calorie_goal * 0.45:
            habit_insights.append(
                "Your recent meals trend calorie-dense. Building one lighter, high-protein meal into the day could improve consistency."
            )

    habit_patterns, habit_suggestions = build_habit_insights([*history_logs, *today_logs])
    health_score, _, _ = calculate_health_score(user, today_logs)
    if health_score < 45:
        nudges.append("Today's health score is low. Aim for a lean protein, fruit, or vegetable in your next meal.")
    elif health_score >= 80:
        suggestions.append("Your health score is strong today. Keep reinforcing the habits behind those choices.")

    if not suggestions:
        suggestions.append("Your food choices look balanced today. Keep prioritizing protein, fiber, and hydration.")

    return (
        list(dict.fromkeys(suggestions)),
        list(dict.fromkeys(nudges)),
        list(dict.fromkeys([*habit_insights, *habit_patterns, *habit_suggestions])),
        health_score,
    )


def filter_logs_for_day(logs: Iterable[FoodLog], target_date: date) -> list[FoodLog]:
    return [log for log in logs if log.consumed_at.date() == target_date]
