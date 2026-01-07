"""
@file test_participations.py
@brief Integration tests for participation-survey API routes.

Tests include:
- Participating in an event (new participation and updating existing)
- Reading event participation statistics
- Retrieving the currently authenticated user's active events
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session

from app.backend.auth_service import get_current_user
from app.database.models.event import Event
from app.database.models.participations import EventParticipation, ParticipationStatus
from app.database.session import get_session
from app.main import app


def override_user(user_id=123):
    fake_user = MagicMock()
    fake_user.id = user_id
    return fake_user


@pytest.mark.asyncio
async def test_participate_in_event_new():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: override_user(999)

    mock_db.exec.return_value.first.return_value = None
    mock_db.add.side_effect = lambda obj: setattr(obj, "id", 1)
    mock_db.refresh.side_effect = lambda obj: None

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/participations/events/1", json={"status": "going"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "going"
    assert data["user_id"] == 999
    assert data["event_id"] == 1
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_participate_in_event_update():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: override_user(111)

    existing_participation = EventParticipation(
        id=1, user_id=111, event_id=1, status=ParticipationStatus.maybe
    )
    mock_db.exec.return_value.first.return_value = existing_participation
    mock_db.commit.side_effect = lambda: None
    mock_db.refresh.side_effect = lambda obj: None

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/participations/events/1", json={"status": "going"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "going"
    assert data["user_id"] == 111
    assert data["event_id"] == 1
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_read_event_participation_stats():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    fake_participants = [
        EventParticipation(user_id=1, event_id=1, status=ParticipationStatus.going),
        EventParticipation(user_id=2, event_id=1, status=ParticipationStatus.maybe),
        EventParticipation(user_id=3, event_id=1, status=ParticipationStatus.not_going),
    ]
    mock_db.exec.return_value.all.return_value = fake_participants

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/participations/events/1/stats")

    assert response.status_code == 200
    data = response.json()
    assert data == {"going": 1, "maybe": 1, "not_going": 1}


@pytest.mark.asyncio
async def test_read_my_active_events():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: override_user(123)

    now = datetime.utcnow()
    event1 = Event(id=1, name="Event 1", location="X", time=now, owner_id=123)
    participation1 = EventParticipation(user_id=123, event_id=1, status=ParticipationStatus.going)
    event2 = Event(id=2, name="Event 2", location="Y", time=now, owner_id=999)
    participation2 = EventParticipation(user_id=123, event_id=2, status=ParticipationStatus.maybe)

    mock_db.exec.return_value.all.return_value = [
        (event1, participation1),
        (event2, participation2),
    ]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/participations/me/events")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["owner_id"] == 123
    assert data[0]["participation_status"] == "going"
    assert data[1]["owner_id"] == 999
    assert data[1]["participation_status"] == "maybe"
