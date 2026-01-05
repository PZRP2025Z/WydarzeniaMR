from fastapi import APIRouter, Depends, Response, Form, Cookie
from sqlmodel import Session

from app.database.session import get_session
from app.backend.auth_service import (
    register_user,
    login_for_access_token,
    get_current_user,
    refresh_access_token,
    logout_user,
)

from app.database.models.user import User
from app.database.models.auth import RegisterUserRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User)
def register_user_route(
    request: RegisterUserRequest,
    response: Response,
    db: Session = Depends(get_session),
):
    return register_user(request, db, response)


@router.post("/token", response_model=Token)
def login_route(
    response: Response,
    mail: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session),
):
    return login_for_access_token(mail, password, db, response)


@router.get("/me")
def read_me(user: User = Depends(get_current_user)):
    return {"user_id": user.id, "login": user.login, "emial": user.email}


@router.post("/refresh")
def refresh_token_route(response: Response, refresh_token: str = Cookie(None)):
    refresh_access_token(refresh_token, response)
    return {"message": "Access token refreshed"}


@router.post("/logout")
def logout_route(response: Response):
    logout_user(response)
    return {"message": "Logged out successfully"}
