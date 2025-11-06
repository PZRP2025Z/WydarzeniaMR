import pytest
from typing import AsyncGenerator
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from app.database.session import get_session
from unittest.mock import MagicMock
from app.database.models.event import Event
from sqlmodel import Session


@pytest.mark.asyncio
async def test_read_events(app: FastAPI):
    # mock database
    fake_events = [Event(id=1, name="Event 1"), Event(id=2, name="Event 2")]
    mock_db = MagicMock(spec=Session)
    mock_exec = mock_db.exec.return_value
    mock_exec.all.return_value = fake_events

    app.dependency_overrides[get_session] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/events/")
    assert response.status_code == 200
