"""
Authentication functionality
"""

import os
import logging
import jwt
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status, Cookie, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.database.models.user import User
from app.database.models.auth import TokenData, RegisterUserRequest, Token

logger = logging.getLogger(__name__)

TOKEN_KEY = os.getenv("TOKEN_KEY", "changeme-secret-key")
TOKEN_ALGORITHM = os.getenv("TOKEN_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))

# JWT config & password hashing
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
argon2_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return argon2_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return argon2_context.hash(password)


def authenticate_user(email: str, password: str, db: Session) -> Optional[User]:
    user = db.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"Authentication failed for email: {email}")
        return None
    return user


def create_access_token(
    email: str, user_id: int, expires_delta: Optional[timedelta] = None
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "sub": email,
        "user_id": user_id,
        "exp": int(expire.timestamp()),  # <-- zamieniamy datetime na timestamp
    }
    encoded_jwt = jwt.encode(to_encode, TOKEN_KEY, algorithm=TOKEN_ALGORITHM)
    logger.debug(f"JWT created for user_id={user_id}")
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, TOKEN_KEY, algorithms=[TOKEN_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("Missing user_id in token")
        return TokenData(user_id=user_id)
    except Exception as e:
        logger.warning(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def register_user(request: RegisterUserRequest, db: Session) -> User:
    existing_user = db.exec(select(User).where(User.email == request.email)).first()
    if existing_user:
        logger.warning(f"Attempt to register existing email: {request.email}")
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(request.password)
    user = User(
        first_name=request.first_name,
        last_name=request.last_name,
        email=request.email,
        hashed_password=hashed_pw,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"New user registered: {user.email}")
    return user


def get_current_user(access_token: Optional[str] = Cookie(None)) -> TokenData:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return verify_token(access_token)


CurrentUser = Annotated[TokenData, Depends(get_current_user)]


def login_for_access_token(form_data, db: Session, response: Response) -> dict:
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        logger.warning(f"Login attempt failed for {form_data.username}")
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_token(
        email=user.email,
        user_id=user.id,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    refresh_token = create_access_token(
        email=user.email,
        user_id=user.id,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # True in production
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # True in production
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    logger.info(f"Issued access + refresh token for {user.email}")
    return {"message": "Logged in"}


def refresh_access_token(refresh_token: str, response: Response) -> str:
    """Verify refresh token and issue a new access token."""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        payload = jwt.decode(refresh_token, TOKEN_KEY, algorithms=[TOKEN_ALGORITHM])
        user_id = payload.get("user_id")
        email = payload.get("sub")
        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    access_token = create_access_token(
        email=email,
        user_id=user_id,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return access_token
