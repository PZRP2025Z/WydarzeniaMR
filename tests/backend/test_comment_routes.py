"""
@file test_comment.py
@brief Integration tests for comment API routes.

Tests cover:
- Adding a comment as an authenticated user
- Retrieving paginated comments for an event
- Attempting to add a comment without authentication
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session

from app.backend.auth_service import get_current_user
from app.database.models.comment import Comment
from app.database.models.user import User
from app.database.session import get_session
from app.main import app


@pytest.mark.asyncio
async def test_add_comment():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    fake_user = MagicMock()
    fake_user.id = 42
    fake_user.login = "tester"

    app.dependency_overrides[get_current_user] = lambda: fake_user

    mock_db.get.return_value = User(id=42, login="tester", email="test@example.com")

    def fake_add(obj):
        obj.id = 1
        obj.created_at = datetime.utcnow()

    mock_db.add.side_effect = fake_add
    mock_db.refresh.side_effect = lambda obj: None
    mock_db.get.return_value = fake_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/events/10/comments",
            json={"content": "Hello world"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["user_login"] == "tester"
    assert data["content"] == "Hello world"


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

    mock_db.get.return_value = User(id=2, login="commenter", email="test@example.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/events/10/comments?limit=10&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert data[0]["user_login"] == "commenter"
    assert data[0]["content"] == "test"


@pytest.mark.asyncio
async def test_add_comment_unauthorized():
    mock_db = MagicMock(spec=Session)
    app.dependency_overrides[get_session] = lambda: mock_db

    app.dependency_overrides.pop(get_current_user, None)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/events/1/comments",
            json={"content": "test"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
