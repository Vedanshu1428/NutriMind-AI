from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from models import User
from schemas import RestaurantSuggestionResponse
from service_layer.cache import restaurant_cache


RESTAURANT_CATALOG = [
    {"name": "Green Bowl Kitchen", "city": "Bengaluru", "country": "India", "lat": 12.9716, "lon": 77.5946, "cuisine": "Bowls", "address": "Indiranagar", "top_picks": ["Protein millet bowl", "Tofu crunch salad"]},
    {"name": "Fresh Fork Cafe", "city": "Mumbai", "country": "India", "lat": 19.076, "lon": 72.8777, "cuisine": "Cafe", "address": "Bandra West", "top_picks": ["Greek yogurt parfait", "Chicken quinoa plate"]},
    {"name": "Lean Lunch Lab", "city": "Delhi", "country": "India", "lat": 28.6139, "lon": 77.209, "cuisine": "Modern Indian", "address": "Connaught Place", "top_picks": ["Tandoori paneer box", "Grilled chicken rice bowl"]},
    {"name": "Harvest Table", "city": "Hyderabad", "country": "India", "lat": 17.385, "lon": 78.4867, "cuisine": "Healthy Casual", "address": "Jubilee Hills", "top_picks": ["Veg power thali", "Salmon greens plate"]},
    {"name": "Whole Plate Studio", "city": "Chennai", "country": "India", "lat": 13.0827, "lon": 80.2707, "cuisine": "Continental", "address": "Nungambakkam", "top_picks": ["Egg white wrap", "Low-carb harvest bowl"]},
    {"name": "Fuel Greens", "city": "Pune", "country": "India", "lat": 18.5204, "lon": 73.8567, "cuisine": "Salads", "address": "Koregaon Park", "top_picks": ["High-protein salad", "Roasted veggie box"]},
]


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    origin = radians(lat1)
    destination = radians(lat2)
    value = sin(delta_lat / 2) ** 2 + cos(origin) * cos(destination) * sin(delta_lon / 2) ** 2
    return 2 * radius * asin(sqrt(value))


def resolve_location(user: User, latitude: float | None, longitude: float | None, city: str | None, country: str | None) -> tuple[float | None, float | None, str]:
    resolved_lat = latitude if latitude is not None else user.latitude
    resolved_lon = longitude if longitude is not None else user.longitude
    resolved_city = city or user.city
    resolved_country = country or user.country or "India"
    label = ", ".join(part for part in [resolved_city, resolved_country] if part) if resolved_city else resolved_country
    return resolved_lat, resolved_lon, label


def get_restaurant_suggestions(
    user: User,
    latitude: float | None = None,
    longitude: float | None = None,
    city: str | None = None,
    country: str | None = None,
) -> RestaurantSuggestionResponse:
    resolved_lat, resolved_lon, location_label = resolve_location(user, latitude, longitude, city, country)
    cache_key = f"user:{user.id}:restaurants:{resolved_lat}:{resolved_lon}:{location_label}"
    cached = restaurant_cache.get(cache_key)
    if cached:
        return RestaurantSuggestionResponse.model_validate({**cached, "cached": True})

    ranked = []
    for restaurant in RESTAURANT_CATALOG:
        if resolved_lat is not None and resolved_lon is not None:
            distance = haversine_distance_km(resolved_lat, resolved_lon, restaurant["lat"], restaurant["lon"])
        elif location_label.lower().find(restaurant["city"].lower()) >= 0:
            distance = 3.5
        else:
            distance = 12.0

        ranked.append(
            {
                "name": restaurant["name"],
                "cuisine": restaurant["cuisine"],
                "address": f'{restaurant["address"]}, {restaurant["city"]}',
                "distance_km": round(distance, 1),
                "why_it_matches": f'Matches your {user.diet_preference.replace("_", " ")} preference with lower-friction healthy meals.',
                "top_picks": restaurant["top_picks"],
            }
        )

    suggestions = sorted(ranked, key=lambda item: item["distance_km"])[:3]
    payload = {"resolved_location": location_label or "your saved area", "suggestions": suggestions}
    restaurant_cache.set(cache_key, payload)
    return RestaurantSuggestionResponse.model_validate({**payload, "cached": False})
