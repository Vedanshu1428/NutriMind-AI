import os
import secrets
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db
from models import User


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
PBKDF2_ITERATIONS = int(os.getenv("PASSWORD_HASH_ITERATIONS", "600000"))
PBKDF2_SCHEME = "pbkdf2_sha256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def _encode_password(password: str, salt: bytes | None = None, iterations: int = PBKDF2_ITERATIONS) -> str:
    salt = salt or secrets.token_bytes(16)
    derived_key = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    encoded_salt = urlsafe_b64encode(salt).decode("ascii")
    encoded_hash = urlsafe_b64encode(derived_key).decode("ascii")
    return f"{PBKDF2_SCHEME}${iterations}${encoded_salt}${encoded_hash}"


def _verify_pbkdf2_password(password: str, hashed_password: str) -> bool:
    try:
        scheme, iterations_str, encoded_salt, encoded_hash = hashed_password.split("$", 3)
        if scheme != PBKDF2_SCHEME:
            return False
        iterations = int(iterations_str)
        salt = urlsafe_b64decode(encoded_salt.encode("ascii"))
        expected_hash = _encode_password(password, salt=salt, iterations=iterations)
        return secrets.compare_digest(expected_hash, hashed_password)
    except (ValueError, TypeError):
        return False


def hash_password(password: str) -> str:
    return _encode_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith(f"{PBKDF2_SCHEME}$"):
        return _verify_pbkdf2_password(plain_password, hashed_password)
    return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user
