from datetime import datetime
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session

from app.backend.auth_service import get_current_user
from app.database.models.comment import Comment
from app.database.session import get_session
from app.main import app


@pytest.mark.asyncio
async def test_add_comment():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    fake_user = MagicMock()
    fake_user.id = 42
    fake_user.login = "testuser"

    app.dependency_overrides[get_current_user] = lambda: fake_user

    def fake_add(obj):
        obj.id = 1

    mock_db.add.side_effect = fake_add
    mock_db.refresh.side_effect = lambda obj: None
    mock_db.get.return_value = fake_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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

    mock_user = MagicMock()
    mock_user.login = "testuser"
    mock_db.get.return_value = mock_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/events/10/comments/?limit=10&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "test"


@pytest.mark.asyncio
async def test_add_comment_unauthorized():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    app.dependency_overrides.pop(get_current_user, None)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/events/1/comments/",
            json={"content": "test"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
