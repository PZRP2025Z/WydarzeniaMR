"""
Authentication functionality
"""

import os
import logging
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Cookie, Response, Depends
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.database.models.user import User
from app.database.models.auth import TokenData, RegisterUserRequest, Token
from app.database.session import get_session

logger = logging.getLogger(__name__)

TOKEN_KEY = os.getenv("TOKEN_KEY", "changeme-secret-key")
TOKEN_ALGORITHM = os.getenv("TOKEN_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))

argon2_context = CryptContext(schemes=["argon2"], deprecated="auto")


# =====================
# PASSWORDS
# =====================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return argon2_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return argon2_context.hash(password)


# =====================
# TOKENS
# =====================


def create_access_token(email: str, user_id: int, expires_delta=None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": email, "user_id": user_id, "exp": int(expire.timestamp())}
    return jwt.encode(payload, TOKEN_KEY, algorithm=TOKEN_ALGORITHM)


def create_refresh_token(email: str, user_id: int) -> str:
    expire = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return create_access_token(email, user_id, expires_delta=expire)


def issue_tokens_and_set_cookies(user: User, response: Response) -> None:
    """Creates access & refresh tokens and sets cookies."""
    access_token = create_access_token(user.email, user.id)
    refresh_token = create_refresh_token(user.email, user.id)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    logger.info(f"Issued access + refresh token for {user.email}")


def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, TOKEN_KEY, algorithms=[TOKEN_ALGORITHM])
        user_id = payload.get("user_id")
        return TokenData(user_id=user_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# =====================
# USER RESOLUTION
# =====================


def authenticate_user(email: str, password: str, db: Session) -> Optional[User]:
    user = db.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_current_user(
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_session),
) -> User:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token_data = verify_token(access_token)
    user = db.get(User, token_data.user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# =====================
# REGISTER / LOGIN / REFRESH
# =====================


def register_user(
    request: RegisterUserRequest, db: Session, response: Response
) -> User:
    existing = db.exec(select(User).where(User.email == request.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        first_name=request.first_name,
        last_name=request.last_name,
        email=request.email,
        hashed_password=get_password_hash(request.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Ustawiamy cookies, ale ZWRACAMY USER (test tego oczekuje)
    issue_tokens_and_set_cookies(user, response)

    return user


def login_for_access_token(
    email: str, password: str, db: Session, response: Response
) -> Token:
    user = authenticate_user(email, password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    issue_tokens_and_set_cookies(user, response)

    # Zwracamy ciało tokena (np. do użycia poza cookies)
    return Token(
        access_token=create_access_token(user.email, user.id),
        token_type="bearer",
    )


def refresh_access_token(refresh_token: str, response: Response) -> str:
    """Verify refresh token and issue a new access token, set in cookie."""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        payload = jwt.decode(refresh_token, TOKEN_KEY, algorithms=[TOKEN_ALGORITHM])
        user_id = payload.get("user_id")
        email = payload.get("sub")
        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    new_access = create_access_token(email=email, user_id=user_id)

    response.set_cookie(
        key="access_token",
        value=new_access,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return new_access
