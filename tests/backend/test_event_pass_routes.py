from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session

from app.backend.auth_service import get_current_user
from app.database.models.event_pass import EventPass
from app.database.models.user import User
from app.database.session import get_session
from app.main import app


@pytest.mark.asyncio
async def test_create_pass_returns_link():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.login = "test"
    mock_user.email = "test@example.com"
    mock_user.hashed_password = "hashed"

    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/passes/personal/123", json={"display_name": "GuestUser"})

    assert response.status_code == 200
    data = response.json()
    assert "link" in data
    assert data["link"].startswith("http")


@pytest.mark.asyncio
async def test_open_pass_unbound():
    mock_db = MagicMock(spec=Session)
    pass_obj = EventPass(
        token_hash="hashedtoken", event_id=123, display_name="GuestUser", user_id=None
    )
    mock_db.exec.return_value.first.return_value = pass_obj
    app.dependency_overrides[get_session] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/passes/faketoken")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unbound"
    assert data["event_id"] == 123
    assert data["display_name"] == "GuestUser"


@pytest.mark.asyncio
async def test_open_pass_bound_guest_auto_login():
    mock_db = MagicMock(spec=Session)
    user = User(id=1, login="Guest", is_guest=True)
    pass_obj = EventPass(
        token_hash="hashedtoken", event_id=123, display_name="GuestUser", user_id=1
    )
    exec_result = MagicMock()
    exec_result.first.return_value = pass_obj
    mock_db.exec.return_value = exec_result
    mock_db.get.return_value = user
    app.dependency_overrides[get_session] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/passes/faketoken")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "logged_in"
    assert data["event_id"] == 123


@pytest.mark.asyncio
async def test_open_pass_bound_regular_user_requires_login():
    mock_db = MagicMock(spec=Session)
    user = User(id=1, login="Regular", is_guest=False)
    pass_obj = EventPass(
        token_hash="hashedtoken", event_id=123, display_name="GuestUser", user_id=1
    )

    exec_result = MagicMock()
    exec_result.first.return_value = pass_obj
    mock_db.exec.return_value = exec_result
    mock_db.get.return_value = user
    app.dependency_overrides[get_session] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/passes/faketoken")

    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "login_required"
    assert data["event_id"] == 123


@pytest.mark.asyncio
async def test_accept_as_guest_creates_user_and_logs_in():
    mock_db = MagicMock(spec=Session)

    pass_obj = EventPass(
        token_hash="hashedtoken",
        event_id=123,
        display_name="GuestUser",
        user_id=None,
    )

    # resolve_event_pass
    exec_result = MagicMock()
    exec_result.first.return_value = pass_obj
    mock_db.exec.return_value = exec_result

    # DB side effects
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None

    # IMPORTANT: login_via_pass lookup
    mock_db.get.return_value = User(
        id=1,
        login="GuestUser",
        is_guest=True,
    )

    app.dependency_overrides[get_session] = lambda: mock_db

    mock_db.refresh.side_effect = (
        lambda obj: setattr(obj, "id", 1) if isinstance(obj, User) and obj.id is None else None
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/passes/faketoken/accept-guest")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "guest_created" or data["status"] == "logged_in"


@pytest.mark.asyncio
async def test_accept_with_existing_login_binds_pass():
    mock_db = MagicMock(spec=Session)
    pass_obj = EventPass(
        token_hash="hashedtoken", event_id=123, display_name="GuestUser", user_id=None
    )
    mock_db.exec.return_value.first.return_value = pass_obj
    fake_user = User(
        id=42, login="ExistingUser", email="user@example.com", hashed_password="hashed"
    )
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_session] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/passes/faketoken/accept-login")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "linked"
