import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient
from httpx import AsyncClient

from database import get_test_engine, get_test_session, Base, get_db
from app.factory import create_app
import models


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = get_test_engine()
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def setup_test_database(test_engine):
    """Set up the test database with all tables."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Clean up - drop all tables
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(setup_test_database, test_engine):
    """Create a fresh database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    
    # Create a session bound to the transaction
    session = Session(bind=connection)
    
    yield session
    
    # Clean up
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create a test client with dependency override."""
    app = create_app()
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(db_session):
    """Create an async test client with dependency override."""
    app = create_app()
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# Test data fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "full_name": "Test User",
        "email": "test@example.com",
        "hashed_password": "hashed_password_123",
        "disabled": False,
        "permissions": ["read", "write"],
        "history": [],
        "query_ids": [1, 2, 3]
    }


@pytest.fixture
def sample_telegram_channel_data():
    """Sample telegram channel data for testing."""
    return {
        "key": "test_channel",
        "value": "test_value",
        "tag": "test_tag",
        "chat_id": 123456789,
        "access_hash": 987654321,
        "in_progress": False,
        "blocked": False,
        "subscribed_by": 1
    }


@pytest.fixture
def sample_telegram_peer_data():
    """Sample telegram peer data for testing."""
    return {
        "username": "test_peer",
        "url": "https://t.me/test_peer",
        "peer_id": 111222333,
        "blocked": False,
        "linked_peer_id": None,
        "subscriber": 1,
        "is_channel": True,
        "on_waiting": False
    }


@pytest.fixture
def sample_user(db_session, sample_user_data):
    """Create a sample user in the database."""
    user = models.User(**sample_user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_telegram_channel(db_session, sample_telegram_channel_data):
    """Create a sample telegram channel in the database."""
    channel = models.TelegramChannel(**sample_telegram_channel_data)
    db_session.add(channel)
    db_session.commit()
    db_session.refresh(channel)
    return channel


@pytest.fixture
def sample_telegram_peer(db_session, sample_telegram_peer_data):
    """Create a sample telegram peer in the database."""
    peer = models.TelegramPeer(**sample_telegram_peer_data)
    db_session.add(peer)
    db_session.commit()
    db_session.refresh(peer)
    return peer 