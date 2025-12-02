"""
User authentication and registration routes
"""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlmodel import Session, select
from fastapi.security import OAuth2PasswordRequestForm
from app.database.session import get_session
from app.database.models.user import User
from app.database.models.auth import RegisterUserRequest, Token
from app.backend.auth_service import (
    register_user,
    login_for_access_token,
    CurrentUser,
    refresh_access_token,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User)
def register_user_route(
    request: RegisterUserRequest, db: Session = Depends(get_session)
):
    return register_user(request=request, db=db)


@router.post("/token")
def login_route(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_session),
):
    return login_for_access_token(form_data, db, response)


@router.get("/me")
def get_me(current_user: CurrentUser):
    return {"user_id": current_user.user_id}


@router.post("/refresh")
def refresh_token_route(response: Response, refresh_token: str = Cookie(None)):
    refresh_access_token(refresh_token, response)
    return {"message": "Access token refreshed"}
