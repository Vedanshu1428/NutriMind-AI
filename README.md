# Smart Nutrition Coach

Smart Nutrition Coach is a full-stack web application that combines food logging, calorie tracking, behavior nudges, rule-based recommendations, and OpenAI-powered nutrition advice.

## Features

- JWT-based signup and login
- User profile capture for age, weight, height, goal, and diet preference
- Daily meal logging with macro and calorie tracking
- Seeded food database with healthy vs junk categorization
- Rule-based recommendation engine with healthier alternatives
- Time-based and behavior-based coaching nudges
- AI endpoint at `/ai-recommend` powered by the OpenAI API
- React dashboard for logs, summaries, nudges, and AI advice

## Backend Setup

1. Open a terminal in [backend](/C:/Users/LENOVO/Documents/New%20project/backend).
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and set your secrets:

```env
DATABASE_URL=sqlite:///./smart_nutrition_coach.db
JWT_SECRET_KEY=replace-with-a-secure-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
FRONTEND_URL=http://localhost:3000
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4.1-mini
DEBUG=0
```

5. Run the API:

```bash
uvicorn main:app --reload
```

The backend starts on `http://localhost:8000`.

## Frontend Setup

1. Open a terminal in [frontend](/C:/Users/LENOVO/Documents/New%20project/frontend).
2. Install dependencies:

```bash
npm install
```

3. Copy `.env.example` to `.env`:

```env
REACT_APP_API_URL=http://localhost:8000
```

4. Start the React app:

```bash
npm start
```

The frontend starts on `http://localhost:3000`.

## Seeded Foods

Use these names in the food logger:

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

## API Endpoints

- `POST /signup`
- `POST /login`
- `POST /log-food`
- `GET /daily-summary`
- `GET /recommendations`
- `POST /ai-recommend`

## Notes

- SQLite is used by default for local development.
- Set a strong `JWT_SECRET_KEY` before deploying.
- For production, place the API behind HTTPS and use PostgreSQL if needed.
