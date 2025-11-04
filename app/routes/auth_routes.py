"""
User authentication and registration routes
"""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from fastapi.security import OAuth2PasswordRequestForm
from app.database.session import get_session
from app.database.models.user import User
from app.database.models.auth import RegisterUserRequest, Token
from app.backend.auth_service import register_user, login_for_access_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User)
def register_user_route(
    request: RegisterUserRequest, db: Session = Depends(get_session)
):
    return register_user(request=request, db=db)


@router.post("/token", response_model=Token)
def login_route(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_session),
):
    return login_for_access_token(form_data, db)
