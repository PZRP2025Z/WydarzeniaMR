"""
@file conftest.py
@brief Pytest fixtures for FastAPI integration tests.

Provides:
- `app`: FastAPI instance with event routes included for testing
- `async_client`: Async HTTP client for sending test requests
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient

from app.routes import event_routes


@pytest.fixture(name="app")
def app() -> FastAPI:
    test_app = FastAPI(title="WydarzeniaMR_API")
    test_app.include_router(event_routes.router)
    return test_app


@pytest_asyncio.fixture(name="async_client")
async def client_fixture(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
