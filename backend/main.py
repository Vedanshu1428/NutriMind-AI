import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import Base, SessionLocal, engine
from routes.ai import router as ai_router
from routes.auth import router as auth_router
from routes.food import router as food_router
from routes.insights import router as insights_router
from routes.product import router as product_router
from routes.recommend import router as recommend_router
from schema_migrations import run_startup_migrations
from seed import seed_food_data


load_dotenv()

app = FastAPI(
    title="Smart Nutrition Coach API",
    version="2.0.0",
    description="A scalable nutrition coaching backend with food logging, weekly plans, restaurants, nudges, analytics, and AI advice.",
)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    run_startup_migrations(engine)
    db = SessionLocal()
    try:
        seed_food_data(db)
    finally:
        db.close()


@app.get("/")
def healthcheck():
    return {"message": "Smart Nutrition Coach API is running"}


@app.exception_handler(Exception)
async def global_exception_handler(_, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc) if os.getenv("DEBUG") == "1" else "Internal server error"})


app.include_router(auth_router, tags=["auth"])
app.include_router(food_router, tags=["food"])
app.include_router(insights_router, tags=["insights"])
app.include_router(recommend_router, tags=["recommendations"])
app.include_router(product_router, tags=["product"])
app.include_router(ai_router, tags=["ai"])
