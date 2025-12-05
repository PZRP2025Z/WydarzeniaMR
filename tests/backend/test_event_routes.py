import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock
from sqlmodel import Session
from app.database.session import get_session
from app.database.models.event import Event
from app.backend.auth_service import get_current_user
from app.main import app


def override_user(user_id=123):
    fake_user = MagicMock()
    fake_user.id = user_id
    return fake_user


@pytest.mark.asyncio
async def test_read_events():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    fake_events = [
        Event(id=1, name="Event 1", location="X", owner_id=10),
        Event(id=2, name="Event 2", location="Y", owner_id=20),
    ]
    mock_exec = mock_db.exec.return_value
    mock_exec.all.return_value = fake_events

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/events/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Event 1"


@pytest.mark.asyncio
async def test_create_event():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: override_user(999)

    def fake_add(obj):
        obj.id = 1

    mock_db.add.side_effect = fake_add
    mock_db.refresh.side_effect = lambda obj: None

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/events/",
            json={"name": "Test Event", "location": "Test Location"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Event"
    assert data["location"] == "Test Location"
    assert data["owner_id"] == 999


@pytest.mark.asyncio
async def test_read_event():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    fake_event = Event(id=1, name="Single Event", location="Berlin", owner_id=50)
    mock_db.get.return_value = fake_event

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/events/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Single Event"
    assert data["location"] == "Berlin"


@pytest.mark.asyncio
async def test_update_event_success():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    app.dependency_overrides[get_current_user] = lambda: override_user(999)

    fake_event = Event(id=1, name="Old Name", location="Old Location", owner_id=999)
    mock_db.get.return_value = fake_event

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            "/events/1",
            json={"name": "New Name", "location": "New Location"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["location"] == "New Location"
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_event_forbidden():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    app.dependency_overrides[get_current_user] = lambda: override_user(111)

    fake_event = Event(id=1, name="Old Name", location="Old Location", owner_id=999)
    mock_db.get.return_value = fake_event

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            "/events/1",
            json={"name": "New Name", "location": "New Location"},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "You are not the owner of this event"


@pytest.mark.asyncio
async def test_delete_event_success():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    app.dependency_overrides[get_current_user] = lambda: override_user(999)

    fake_event = Event(id=1, name="Event to Delete", location="Prague", owner_id=999)
    mock_db.get.return_value = fake_event

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete("/events/1")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    mock_db.delete.assert_called_once_with(fake_event)
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_event_forbidden():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    app.dependency_overrides[get_current_user] = lambda: override_user(111)

    fake_event = Event(id=1, name="Event to Delete", location="Prague", owner_id=999)
    mock_db.get.return_value = fake_event

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete("/events/1")

    assert response.status_code == 403
    assert response.json()["detail"] == "You are not the owner of this event"


@pytest.mark.asyncio
async def test_create_event_unauthorized():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    app.dependency_overrides.pop(get_current_user, None)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/events/", json={"name": "Hack", "location": "Nowhere"}
        )

    assert response.status_code == 401
