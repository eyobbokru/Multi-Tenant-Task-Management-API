# /app/tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from redis import Redis
from app.db.base import Base

# Test database URL (adjust according to your docker-compose setup)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/test_db"

# Create async engine for tests
test_engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    """Create test database engine."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for a test."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()
        await session.close()

@pytest.fixture
def redis() -> Generator[Redis, None, None]:
    """Create a Redis connection for testing."""
    redis_client = Redis(
        host='redis',  # Use service name from docker-compose
        port=6379,
        db=1,  # Use different DB for testing
        decode_responses=True
    )
    try:
        redis_client.ping()
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")
    
    redis_client.flushdb()  # Clear test database
    yield redis_client
    redis_client.flushdb()  # Clean up after tests
    redis_client.close()