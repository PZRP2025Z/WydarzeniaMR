import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock
from sqlmodel import Session
from app.main import app
from app.database.session import get_session
from app.database.models.comment import Comment
from datetime import datetime
from app.backend.auth_service import get_current_user


@pytest.mark.asyncio
async def test_add_comment():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    # Fake authenticated user
    fake_user = MagicMock()
    fake_user.id = 42

    # OVERRIDE działa tylko jeśli kluczem jest prawdziwa funkcja zależności
    app.dependency_overrides[get_current_user] = lambda: fake_user

    # simulate DB add + refresh
    def fake_add(obj):
        obj.id = 1

    mock_db.add.side_effect = fake_add
    mock_db.refresh.side_effect = lambda obj: None

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/events/10/comments/",
            json={"content": "Hello world"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert body["content"] == "Hello world"


@pytest.mark.asyncio
async def test_get_comments_paginated():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    mock_db.exec.return_value.all.return_value = [
        Comment(
            id=1,
            event_id=10,
            user_id=2,
            content="test",
            created_at=datetime.utcnow(),
        )
    ]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/events/10/comments/?limit=10&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "test"
