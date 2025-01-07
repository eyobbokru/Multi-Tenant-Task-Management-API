import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from redis import Redis
from app.db.base import Base
from sqlalchemy.pool import NullPool

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:changeme@db:5432/test_taskmanagement"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=True,
    poolclass=NullPool  # Disable connection pooling
)

TestingSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,  # Explicit transaction control
    autoflush=False    # Explicitly set to False for consistency
)


  
@pytest.fixture(scope="session")
def event_loop():
    """Create a new event loop for the session scope."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Clear first
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

@pytest.fixture(scope="function")
async def db_session():
    """Create a fresh database session for each test."""
    async with TestingSessionLocal() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest.fixture
def redis() -> Generator[Redis, None, None]:
    redis_client = Redis(
        host='redis',
        port=6379,
        db=1,
        decode_responses=True,
        health_check_interval=30  # Added health check
    )
    try:
        redis_client.ping()
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")
    
    redis_client.flushdb()
    yield redis_client
    redis_client.flushdb()
    redis_client.close()