from sqlalchemy.orm import Session

from models import FoodItem


FOOD_DATA = [
    {"name": "Pizza", "calories": 285, "category": "junk", "protein": 12, "carbs": 36, "fats": 10, "healthier_alternative": "Grilled chicken salad"},
    {"name": "Burger", "calories": 295, "category": "junk", "protein": 17, "carbs": 30, "fats": 13, "healthier_alternative": "Turkey lettuce wrap"},
    {"name": "Soda", "calories": 150, "category": "junk", "protein": 0, "carbs": 39, "fats": 0, "healthier_alternative": "Fresh lime water"},
    {"name": "French Fries", "calories": 312, "category": "junk", "protein": 3, "carbs": 41, "fats": 15, "healthier_alternative": "Baked sweet potato wedges"},
    {"name": "Ice Cream", "calories": 207, "category": "junk", "protein": 4, "carbs": 24, "fats": 11, "healthier_alternative": "Greek yogurt with berries"},
    {"name": "Salad", "calories": 120, "category": "healthy", "protein": 5, "carbs": 14, "fats": 5, "healthier_alternative": None},
    {"name": "Oatmeal", "calories": 154, "category": "healthy", "protein": 6, "carbs": 28, "fats": 3, "healthier_alternative": None},
    {"name": "Grilled Chicken", "calories": 165, "category": "healthy", "protein": 31, "carbs": 0, "fats": 4, "healthier_alternative": None},
    {"name": "Egg Omelette", "calories": 190, "category": "healthy", "protein": 13, "carbs": 2, "fats": 14, "healthier_alternative": None},
    {"name": "Fruit Smoothie", "calories": 180, "category": "healthy", "protein": 4, "carbs": 38, "fats": 2, "healthier_alternative": None},
    {"name": "Brown Rice Bowl", "calories": 216, "category": "healthy", "protein": 5, "carbs": 45, "fats": 2, "healthier_alternative": None},
    {"name": "Greek Yogurt", "calories": 100, "category": "healthy", "protein": 17, "carbs": 6, "fats": 0, "healthier_alternative": None},
]


def seed_food_data(db: Session) -> None:
    existing_count = db.query(FoodItem).count()
    if existing_count > 0:
        return

    for item in FOOD_DATA:
        db.add(FoodItem(**item))

    db.commit()
