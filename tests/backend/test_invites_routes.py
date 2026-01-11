"""
@file test_invites.py
@brief Integration tests for event invitation (reusable, account-only) API routes.

Tests include:
- Creating a reusable event invitation
- Opening an invitation (resolving token to get event details)
- Accepting an invitation with an authenticated user
"""

from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session
from unittest.mock import patch

from app.backend.auth_service import get_current_user
from app.database.models.event_invitation import EventInvitation
from app.database.models.user import User
from app.database.session import get_session
from app.main import app


@pytest.mark.asyncio
async def test_create_invite_returns_link():
    """Test that creating an invitation returns a valid link."""
    mock_db = MagicMock(spec=Session)
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.login = "test"
    mock_user.email = "test@example.com"
    mock_user.hashed_password = "hashed"

    app.dependency_overrides[get_session] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/invites/", json={"event_id": 123})

    assert response.status_code == 200
    data = response.json()
    assert "link" in data
    assert data["link"].startswith("http")
    assert "/invite/" in data["link"]


@pytest.mark.asyncio
async def test_open_invite_returns_event_details():
    """Test that opening an invitation returns event information."""
    mock_db = MagicMock(spec=Session)
    invitation_obj = EventInvitation(
        token_hash="hashedtoken",
        event_id=456,
    )
    exec_result = MagicMock()
    exec_result.first.return_value = invitation_obj
    mock_db.exec.return_value = exec_result

    app.dependency_overrides[get_session] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/invites/faketoken")

    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == 456


@pytest.mark.asyncio
async def test_open_invite_no_authentication_required():
    """Test that opening an invitation doesn't require authentication."""
    mock_db = MagicMock(spec=Session)
    invitation_obj = EventInvitation(
        token_hash="hashedtoken",
        event_id=789,
    )
    exec_result = MagicMock()
    exec_result.first.return_value = invitation_obj
    mock_db.exec.return_value = exec_result

    app.dependency_overrides[get_session] = lambda: mock_db
    # Explicitly not setting get_current_user override

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/invites/faketoken")

    assert response.status_code == 200
    data = response.json()
    assert "event_id" in data


@pytest.mark.asyncio
@patch("app.backend.participations_service.notify_participant_joined")
async def test_accept_invitation_with_authenticated_user(mock_notify):
    """Test that an authenticated user can accept an invitation."""
    mock_db = MagicMock(spec=Session)

    invitation_obj = EventInvitation(
        token_hash="hashedtoken",
        event_id=123,
    )

    invitation_exec_result = MagicMock()
    invitation_exec_result.first.return_value = invitation_obj

    participation_exec_result = MagicMock()
    participation_exec_result.first.return_value = None

    mock_db.exec.side_effect = [
        invitation_exec_result,
        participation_exec_result,
    ]

    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None

    fake_user = User(
        id=42,
        login="ExistingUser",
        email="user@example.com",
        hashed_password="hashed",
        is_guest=False,
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_session] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/invites/faketoken/accept")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["event_id"] == 123


@pytest.mark.asyncio
async def test_accept_invitation_requires_authentication():
    """Test that accepting an invitation requires an authenticated user."""
    mock_db = MagicMock(spec=Session)

    invitation_obj = EventInvitation(
        token_hash="hashedtoken",
        event_id=123,
    )

    exec_result = MagicMock()
    exec_result.first.return_value = invitation_obj
    mock_db.exec.return_value = exec_result

    app.dependency_overrides[get_session] = lambda: mock_db
    # Not setting get_current_user, simulating unauthenticated request
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/invites/faketoken/accept")

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
@patch("app.backend.participations_service.notify_participant_joined")
async def test_accept_invitation_multiple_users(mock_notify):
    """Test that multiple users can accept the same invitation."""
    mock_db = MagicMock(spec=Session)

    invitation_obj = EventInvitation(
        token_hash="hashedtoken",
        event_id=999,
    )

    # First user accepts
    invitation_exec_result_1 = MagicMock()
    invitation_exec_result_1.first.return_value = invitation_obj

    participation_exec_result_1 = MagicMock()
    participation_exec_result_1.first.return_value = None

    mock_db.exec.side_effect = [
        invitation_exec_result_1,
        participation_exec_result_1,
    ]

    user1 = User(
        id=1,
        login="User1",
        email="user1@example.com",
        hashed_password="hashed",
        is_guest=False,
    )

    app.dependency_overrides[get_current_user] = lambda: user1
    app.dependency_overrides[get_session] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response1 = await client.post("/invites/faketoken/accept")

    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["status"] == "accepted"

    # Second user accepts the same invitation
    invitation_exec_result_2 = MagicMock()
    invitation_exec_result_2.first.return_value = invitation_obj

    participation_exec_result_2 = MagicMock()
    participation_exec_result_2.first.return_value = None

    mock_db.exec.side_effect = [
        invitation_exec_result_2,
        participation_exec_result_2,
    ]

    user2 = User(
        id=2,
        login="User2",
        email="user2@example.com",
        hashed_password="hashed",
        is_guest=False,
    )

    app.dependency_overrides[get_current_user] = lambda: user2

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response2 = await client.post("/invites/faketoken/accept")

    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["status"] == "accepted"
    assert data2["event_id"] == 999
