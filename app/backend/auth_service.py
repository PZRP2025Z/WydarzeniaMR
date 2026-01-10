"""
@file auth_service.py
@brief Backend authentication functionality and JWT token management.

This module provides functions for password hashing, JWT token creation and
verification, user authentication, login, registration, and logout operations.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Cookie, Depends, HTTPException, Response
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.database.models.auth import TokenData, TokenResponse, UserRegister
from app.database.models.user import User
from app.database.session import get_session

logger = logging.getLogger(__name__)

TOKEN_KEY = os.getenv("TOKEN_KEY", "changeme-secret-key")
TOKEN_ALGORITHM = os.getenv("TOKEN_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 5))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

ACCESS_TOKEN_KEY = "access_token"
REFRESH_TOKEN_KEY = "refresh_token"

argon2_context = CryptContext(schemes=["argon2"], deprecated="auto")


####################### PASSWORDS #######################


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    @brief Verify a plain password against a hashed password.

    @param plain_password Password provided by the user.
    @param hashed_password Stored hashed password.

    @return True if the password matches, False otherwise.
    """
    return argon2_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    @brief Hash a plain password using Argon2.

    @param password Password to hash.

    @return Hashed password as a string.
    """
    return argon2_context.hash(password)


######################## TOKENS  ########################


def create_access_token(email: str, user_id: int) -> str:
    """
    @brief Create a short-living access token for authentication.

    @param email User's email.
    @param user_id User's ID.

    @return JWT access token as a string.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": email, "user_id": user_id, "exp": int(expire.timestamp()), "type": "access"}
    logger.info("New access token issued")
    return jwt.encode(payload, TOKEN_KEY, algorithm=TOKEN_ALGORITHM)


def create_refresh_token(email: str, user_id: int) -> str:
    """
    @brief Create a long-living refresh token used to generate new access tokens.

    @param email User's email.
    @param user_id User's ID.

    @return JWT refresh token as a string.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": email, "user_id": user_id, "exp": int(expire.timestamp()), "type": "refresh"}
    logger.info("New refresh token issued")
    return jwt.encode(payload, TOKEN_KEY, algorithm=TOKEN_ALGORITHM)


def issue_tokens_and_set_cookies(user: User, response: Response) -> None:
    """
    @brief Issue both access and refresh tokens and set them as HTTP-only cookies.

    @param user Authenticated user for whom the tokens are issued.
    @param response FastAPI Response object used to set cookies.
    """
    access_token = create_access_token(user.email, user.id)
    refresh_token = create_refresh_token(user.email, user.id)
    # Access token
    response.set_cookie(
        key=ACCESS_TOKEN_KEY,
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    # Refresh token
    response.set_cookie(
        key=REFRESH_TOKEN_KEY,
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )
    logger.info("Cookies set for new tokens")


def verify_token(token: str) -> TokenData:
    """
    @brief Verify a JWT token and extract user data.

    @param token JWT token string to verify.

    @return TokenData object containing user_id.

    @throws HTTPException 401 if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, TOKEN_KEY, algorithms=[TOKEN_ALGORITHM])
        user_id = payload.get("user_id")
        logger.info("Token successfully verified")
        return TokenData(user_id=user_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from None


def refresh_access_token(refresh_token: str, response: Response) -> str:
    """
    @brief Refresh the access token using a valid refresh token.

    If the access token has expired, verifies the refresh token and issues a new
    access token, setting it in the response cookies.

    @param refresh_token JWT refresh token.
    @param response FastAPI Response object used to set the new access token cookie.

    @return New JWT access token as a string.

    @throws HTTPException 401 if refresh token is missing, invalid, or expired.
    """
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(refresh_token, TOKEN_KEY, algorithms=[TOKEN_ALGORITHM])
        user_id = payload.get("user_id")
        email = payload.get("sub")
        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from None
    new_access = create_access_token(email=email, user_id=user_id)
    # Set access token cookie
    response.set_cookie(
        key=ACCESS_TOKEN_KEY,
        value=new_access,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    logger.info("Access token refreshed by refresh token")
    return new_access


############### LOGIN/REGISTER MANAGEMENT ###############


def get_current_user(
    access_token: str | None = Cookie(None),
    refresh_token: str | None = Cookie(None),
    db: Session = Depends(get_session),
    response: Response = None,
) -> User:
    """
    @brief Retrieve the currently authenticated user based on access token.

    If the access token is expired but a valid refresh token exists,
    it issues a new access token.

    @param access_token JWT access token from cookies.
    @param refresh_token JWT refresh token from cookies.
    @param db Database session dependency.
    @param response FastAPI Response object used to refresh access token if needed.

    @return User object representing the currently authenticated user.

    @throws HTTPException 401 if no valid tokens are present or user not found.
    """
    if response is None:
        response = Response()

    if not access_token:
        if refresh_token:
            access_token = refresh_access_token(refresh_token, response)
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        token_data = verify_token(access_token)
    except HTTPException:
        if refresh_token:
            access_token = refresh_access_token(refresh_token, response)
            token_data = verify_token(access_token)
        else:
            raise
    user = db.get(User, token_data.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    logger.info("User identified by access token")
    return user


def register_user(request: UserRegister, db: Session, response: Response) -> User:
    """
    @brief Register a new user and issue JWT tokens.

    @param request UserRegister Pydantic model containing registration info.
    @param db Database session dependency.
    @param response FastAPI Response object used to set authentication cookies.

    @return Newly created User object.

    @throws HTTPException 400 if the email is already registered.
    """
    existing = db.exec(select(User).where(User.email == request.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        login=request.login,
        email=request.email,
        hashed_password=get_password_hash(request.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    issue_tokens_and_set_cookies(user, response)
    logger.info("New user registered")
    return user


def authenticate_user(email: str, password: str, db: Session) -> User | None:
    """
    @brief Authenticate a user with email and password.

    @param email User's email.
    @param password User's password.
    @param db Database session dependency.

    @return User object if authentication is successful, None otherwise.
    """
    user = db.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    logger.info("User successfully authenticated")
    return user


def login_for_access_token(
    email: str, password: str, db: Session, response: Response
) -> TokenResponse:
    """
    @brief Log in a user and issue JWT tokens as cookies.

    @param email User's email.
    @param password User's password.
    @param db Database session dependency.
    @param response FastAPI Response object used to set authentication cookies.

    @return TokenResponse object containing access token and token type.

    @throws HTTPException 401 if authentication fails.
    """
    user = authenticate_user(email, password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    issue_tokens_and_set_cookies(user, response)
    response = TokenResponse(
        access_token=create_access_token(user.email, user.id),
        token_type="bearer",
    )
    logger.info("User logged in")
    return response


def logout_user(response: Response) -> None:
    """
    @brief Log out a user by deleting authentication cookies.

    @param response FastAPI Response object used to delete cookies.
    """
    response.delete_cookie(key=ACCESS_TOKEN_KEY, path="/")
    response.delete_cookie(key=REFRESH_TOKEN_KEY, path="/")
    logger.info("User logged out: cookies deleted")
