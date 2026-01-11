"""
@file conftest.py
@brief Pytest fixtures for FastAPI integration tests.

Provides:
- `app`: FastAPI instance with event routes included for testing
- `async_client`: Async HTTP client for sending test requests
"""

from collections.abc import AsyncGenerator

import dramatiq
import pytest
import pytest_asyncio
from dramatiq.brokers.stub import StubBroker
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


@pytest.fixture(scope="session", autouse=True)
def setup_test_broker():
    """Set up stub broker before any test modules are imported."""
    stub_broker = StubBroker()
    stub_broker.emit_after("process_boot")
    dramatiq.set_broker(stub_broker)
    yield
    stub_broker.close()


@pytest.fixture(autouse=True)
def clean_broker_queues():
    """Clean broker queues between tests."""
    broker = dramatiq.get_broker()
    if isinstance(broker, StubBroker):
        broker.flush_all()
    yield
