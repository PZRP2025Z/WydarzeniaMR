import pytest
from httpx import AsyncClient, ASGITransport
from app.database.session import get_session
from unittest.mock import MagicMock
from app.database.models.event import Event
from sqlmodel import Session
from app.main import app


# GET (all)
@pytest.mark.asyncio
async def test_read_events():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    fake_events = [Event(id=1, name="Event 1"), Event(id=2, name="Event 2")]
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


# CREATE
@pytest.mark.asyncio
async def test_create_event():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

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


# GET (single)
@pytest.mark.asyncio
async def test_read_event():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    fake_event = Event(id=1, name="Single Event", location="Berlin")
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


# UPDATE
@pytest.mark.asyncio
async def test_update_event():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    fake_event = Event(id=1, name="Old Name", location="Old Location")
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


# DELETE
@pytest.mark.asyncio
async def test_delete_event():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    fake_event = Event(id=1, name="Event to Delete", location="Prague")
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
