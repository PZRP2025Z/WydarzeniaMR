"""
@file auth_routes.py
@brief API routes for authentication and JWT management.

Provides endpoints for:
- User registration
- Login and token issuance
- Refreshing access tokens
- Retrieving current authenticated user
- Logging out
"""

from fastapi import APIRouter, Cookie, Depends, Form, Response
from sqlmodel import Session

from app.backend.auth_service import (
    get_current_user,
    login_for_access_token,
    logout_user,
    refresh_access_token,
    register_user,
)
from app.database.models.auth import TokenResponse, UserRegister
from app.database.models.user import User
from app.database.session import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User)
def register_user_route(
    request: UserRegister,
    response: Response,
    db: Session = Depends(get_session),
):
    """
    @brief Register a new user.

    Creates a new user in the database, hashes the password,
    issues access and refresh tokens, and sets cookies.

    @param request User registration data (login, email, password).
    @param response FastAPI Response object for setting cookies.
    @param db Database session dependency.

    @return The newly created User object.
    """
    return register_user(request, db, response)


@router.post("/token", response_model=TokenResponse)
def login_route(
    response: Response,
    mail: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session),
):
    """
    @brief Login user and issue access token.

    Authenticates the user by email and password, sets JWT cookies,
    and returns access token data.

    @param mail User email (form data).
    @param password User password (form data).
    @param response FastAPI Response object for setting cookies.
    @param db Database session dependency.

    @return TokenResponse object with access_token and token_type.
    """
    return login_for_access_token(mail, password, db, response)


@router.get("/me")
def read_me(user: User = Depends(get_current_user)):
    """
    @brief Retrieve currently authenticated user.

    Uses the access token from cookies to identify the user.

    @param user Current authenticated User model (injected via dependency).

    @return Dictionary containing user_id, login, and email.
    """
    return {"user_id": user.id, "login": user.login, "email": user.email}


@router.post("/refresh")
def refresh_token_route(response: Response, refresh_token: str = Cookie(None)):
    """
    @brief Refresh the access token using the refresh token.

    Validates the refresh token, issues a new access token,
    and sets it in the cookies.

    @param refresh_token Refresh token from cookies.
    @param response FastAPI Response object for setting cookies.

    @return JSON message indicating the token has been refreshed.
    """
    refresh_access_token(refresh_token, response)
    return {"message": "Access token refreshed"}


@router.post("/logout")
def logout_route(response: Response):
    """
    @brief Logout the current user.

    Deletes access and refresh token cookies to log out the user.

    @param response FastAPI Response object used to delete cookies.

    @return JSON message confirming successful logout.
    """
    logout_user(response)
    return {"message": "Logged out successfully"}
