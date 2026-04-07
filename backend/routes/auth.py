from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import AuthResponse, UserLogin, UserProfile, UserSignup
from security import create_access_token, hash_password, verify_password


router = APIRouter()


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserSignup, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        age=payload.age,
        weight=payload.weight,
        height=payload.height,
        goal=payload.goal,
        diet_preference=payload.diet_preference,
        city=payload.city,
        country=payload.country,
        latitude=payload.latitude,
        longitude=payload.longitude,
        notification_opt_in=payload.notification_opt_in,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return AuthResponse(access_token=token, user=UserProfile.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id)})
    return AuthResponse(access_token=token, user=UserProfile.model_validate(user))
