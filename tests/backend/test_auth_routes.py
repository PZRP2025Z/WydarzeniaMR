import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock
from sqlmodel import Session

from app.backend.auth_service import get_password_hash, get_current_user
from app.database.session import get_session
from app.database.models.user import User
from app.main import app


@pytest.mark.asyncio
async def test_register_user_success():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    # No existing user
    mock_db.exec.return_value.first.return_value = None

    # Simulate DB add + commit + refresh
    def fake_add(user):
        user.id = 1

    mock_db.add.side_effect = fake_add
    mock_db.refresh.side_effect = lambda user: None

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/auth/register",
            json={
                "first_name": "string",
                "last_name": "string",
                "email": "john@example.com",
                "password": "string",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "john@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_user_duplicate_email():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    # Simulate existing user
    mock_db.exec.return_value.first.return_value = User(
        id=1,
        email="john@example.com",
        first_name="John",
        last_name="Doe",
        hashed_password="hashed",
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/auth/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": "secret123",
            },
        )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_login_invalid_password():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    fake_user = User(
        id=1,
        email="user@example.com",
        hashed_password=get_password_hash("correctpwd"),
    )

    mock_db.exec.return_value.first.return_value = fake_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/auth/token",
            data={
                "username": "user@example.com",
                "password": "wrongpwd",
                "grant_type": "password",
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_sets_cookie():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    # Fake user
    fake_user = User(
        id=1,
        email="user@example.com",
        hashed_password=get_password_hash("correctpwd"),
    )
    mock_db.exec.return_value.first.return_value = fake_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/auth/token",
            data={
                "username": "user@example.com",
                "password": "correctpwd",  # tutaj MUSI być poprawne hasło
                "grant_type": "password",
            },
        )

    assert response.status_code == 200

    # Check that both cookies are set
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie_header
    assert "refresh_token=" in set_cookie_header


@pytest.mark.asyncio
async def test_login_with_cookie_access():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    fake_user = User(
        id=1,
        email="user@example.com",
        hashed_password=get_password_hash("correctpwd"),
    )
    mock_db.exec.return_value.first.return_value = fake_user

    app.dependency_overrides[get_current_user] = lambda: fake_user

    # LOGIN — get cookie
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        login_response = await client.post(
            "/auth/token",
            data={
                "username": "user@example.com",
                "password": "correctpwd",  # poprawne hasło
                "grant_type": "password",
            },
        )

    assert login_response.status_code == 200

    # extract cookie
    set_cookie = login_response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    cookie_value = set_cookie.split("access_token=")[1].split(";")[0]

    cookies = {"access_token": cookie_value}

    # ACCESS protected /auth/me
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", cookies=cookies
    ) as client:
        protected_response = await client.get("/auth/me")

    assert protected_response.status_code == 200
    assert protected_response.json()["user_id"] == 1


@pytest.mark.asyncio
async def test_refresh_access_token():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    fake_user = User(
        id=1,
        email="user@example.com",
        hashed_password=get_password_hash("correctpwd"),
    )
    mock_db.exec.return_value.first.return_value = fake_user

    # LOGIN — pobierz refresh token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        login_response = await client.post(
            "/auth/token",
            data={
                "username": "user@example.com",
                "password": "correctpwd",  # poprawne hasło
                "grant_type": "password",
            },
        )

    set_cookie = login_response.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie
    refresh_cookie_value = set_cookie.split("refresh_token=")[1].split(";")[0]

    # REFRESH
    cookies = {"refresh_token": refresh_cookie_value}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", cookies=cookies
    ) as client:
        refresh_response = await client.post("/auth/refresh")

    assert refresh_response.status_code == 200
    assert refresh_response.json()["message"] == "Access token refreshed"
    new_access_cookie = refresh_response.headers.get("set-cookie", "")
    assert "access_token=" in new_access_cookie
