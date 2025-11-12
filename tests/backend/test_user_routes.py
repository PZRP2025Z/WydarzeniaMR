import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock
from sqlmodel import Session
from app.database.session import get_session
from app.database.models.user import User, PasswordChange
from app.main import app
from app.backend.auth_service import get_password_hash


# GET (all)
@pytest.mark.asyncio
async def test_read_users():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    fake_users = [
        User(id=1, first_name="Alice", last_name="Smith", email="alice@example.com"),
        User(id=2, first_name="Bob", last_name="Jones", email="bob@example.com"),
    ]
    mock_exec = mock_db.exec.return_value
    mock_exec.all.return_value = fake_users

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/users/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["email"] == "alice@example.com"


# GET (single)
@pytest.mark.asyncio
async def test_read_user():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    fake_user = User(
        id=1, first_name="Alice", last_name="Smith", email="alice@example.com"
    )
    mock_db.get.return_value = fake_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/users/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["email"] == "alice@example.com"


# UPDATE
@pytest.mark.asyncio
async def test_update_password_success():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    # Fake user with hashed password
    hashed_pw = get_password_hash("oldpassword")
    fake_user = User(
        id=1,
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
        hashed_password=hashed_pw,
    )
    mock_db.get.return_value = fake_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            "/users/1/password",
            json={
                "current_password": "oldpassword",
                "new_password": "newpassword123",
                "new_password_confirm": "newpassword123",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    mock_db.add.assert_called_once_with(fake_user)
    mock_db.commit.assert_called_once()


# CHANGE password failure (wrong current)
@pytest.mark.asyncio
async def test_update_password_failure_wrong_current():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    hashed_pw = get_password_hash("oldpassword")
    fake_user = User(
        id=1,
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
        hashed_password=hashed_pw,
    )
    mock_db.get.return_value = fake_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            "/users/1/password",
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123",
                "new_password_confirm": "newpassword123",
            },
        )

    assert response.status_code == 400
    data = response.json()
    assert "Password change failed" in data["detail"]


# DELETE
@pytest.mark.asyncio
async def test_delete_user():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    fake_user = User(
        id=1, first_name="Alice", last_name="Smith", email="alice@example.com"
    )
    mock_db.get.return_value = fake_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete("/users/1")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    mock_db.delete.assert_called_once_with(fake_user)
    mock_db.commit.assert_called_once()
