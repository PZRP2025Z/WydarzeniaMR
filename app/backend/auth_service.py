"""
Authentication functionality
"""

import os
import logging
import jwt
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.database.models.user import User
from app.database.models.auth import TokenData, RegisterUserRequest, Token

logger = logging.getLogger(__name__)

TOKEN_KEY = os.getenv("TOKEN_KEY", "changeme-secret-key")
TOKEN_ALGORITHM = os.getenv("TOKEN_ALGORITHM", "HS256")
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))

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
        expires_delta or timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"sub": email, "user_id": user_id, "exp": expire}
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


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]) -> TokenData:
    return verify_token(token)


CurrentUser = Annotated[TokenData, Depends(get_current_user)]


def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session,
) -> Token:
    """Authenticate user and return a JWT token."""
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        logger.warning(f"Login failed for email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        user.email, user.id, expires_delta=timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    )

    logger.info(f"Access token issued for user: {user.email}")
    return Token(access_token=access_token, token_type="bearer")
