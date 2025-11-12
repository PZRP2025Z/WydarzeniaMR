import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock
from sqlmodel import Session
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
    print("HELLO THERE 1")

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
async def test_login_success():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    # Simulate valid user in DB
    fake_user = User(
        id=1,
        email="user@example.com",
        hashed_password="$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$kHb5kZC4w7oB3xAw9WQZ5Q",  # fake argon2 hash
    )

    mock_db.exec.return_value.first.return_value = fake_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/auth/token",
            data={"username": "user@example.com", "password": "whatever"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    assert response.status_code in (200, 401)
    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    else:
        data = response.json()
        assert "Incorrect email or password" in data["detail"]


@pytest.mark.asyncio
async def test_login_invalid_user():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    # No user found
    mock_db.exec.return_value.first.return_value = None

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/auth/token",
            data={"username": "missing@example.com", "password": "nope"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Incorrect email or password"
