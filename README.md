# Smart Nutrition Coach

Smart Nutrition Coach is a full-stack nutrition coaching app with a FastAPI backend and React frontend. It helps users log meals, track calories and macros, receive rule-based nudges, view weekly analytics, and get habit-aware recommendations.

## Current Status

- Backend runs on Python 3.11
- Frontend runs on Node.js LTS
- Core APIs are working locally
- React frontend builds and serves correctly
- The OpenAI-powered `/ai-recommend` route requires a working `OPENAI_API_KEY` and outbound API access

## Features

- JWT-based signup and login
- User profiles with age, weight, height, goal, diet preference, and location preferences
- Food logging with calories, protein, carbs, and fats
- Seeded food database with healthy vs junk classification
- Rule-based food recommendations and healthier alternatives
- Time-based and behavior-based nudges
- Health score and habit insights
- Weekly diet plan generation
- Weekly analytics trends
- Notification feed for habit nudges
- Restaurant suggestions based on saved location
- AI nutrition advice via OpenAI

## Project Structure

- [backend](C:/Users/LENOVO/Documents/New%20project/backend)
- [frontend](C:/Users/LENOVO/Documents/New%20project/frontend)

## Backend Setup

1. Open a terminal in [backend](C:/Users/LENOVO/Documents/New%20project/backend).
2. Create a Python 3.11 virtual environment if needed:

```bash
py -3.11 -m venv .venv
```

3. Install dependencies:

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and configure values:

```env
DATABASE_URL=sqlite:///./smart_nutrition_coach.db
JWT_SECRET_KEY=replace-with-a-secure-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
FRONTEND_URL=http://localhost:3000,http://127.0.0.1:3000
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4.1-mini
OPENAI_VISION_MODEL=gpt-4.1-mini
PASSWORD_HASH_ITERATIONS=600000
DEBUG=0
```

5. Start the backend:

```bash
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Backend URL:

- [http://127.0.0.1:8000](http://127.0.0.1:8000)
- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Frontend Setup

1. Open a terminal in [frontend](C:/Users/LENOVO/Documents/New%20project/frontend).
2. Install dependencies:

```bash
npm install
```

3. Copy `.env.example` to `.env`:

```env
REACT_APP_API_URL=http://127.0.0.1:8000
```

4. Start the frontend:

```bash
npm start
```

Frontend URL:

- [http://localhost:3000](http://localhost:3000)

## Core API Endpoints

- `POST /signup`
- `POST /login`
- `POST /log-food`
- `POST /scan-food`
- `GET /daily-summary`
- `GET /recommendations`
- `GET /habit-insights`
- `GET /health-score`
- `GET /weekly-diet-plan`
- `GET /restaurants/suggestions`
- `GET /notifications/feed`
- `POST /notifications/{notification_id}/read`
- `GET /analytics/weekly-trends`
- `PATCH /profile/preferences`
- `POST /ai-recommend`

## Seeded Foods

- Pizza
- Burger
- Soda
- French Fries
- Ice Cream
- Salad
- Oatmeal
- Grilled Chicken
- Egg Omelette
- Fruit Smoothie
- Brown Rice Bowl
- Greek Yogurt

## Verified Local Flow

The current local setup has been verified for:

- signup
- login
- log food
- daily summary
- recommendations
- health score
- habit insights
- weekly diet plan
- weekly analytics
- frontend build
- frontend page load

## Notes

- SQLite is the default local database.
- The backend is intended to run from the project virtualenv, not the global Python installation.
- Password hashing uses standard-library PBKDF2 for stable cross-platform behavior.
- The AI endpoint may fail if `OPENAI_API_KEY` is missing or outbound API access is blocked.
