from app.db.session import get_db
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from redis import Redis
from app.db.base import Base
from sqlalchemy.pool import NullPool
from main import app
from fastapi.testclient import TestClient
from app.core.config import settings
from sqlalchemy.orm import Session


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


from main import app
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

@pytest.fixture(autouse=True)
async def session_transaction():
    async with test_engine.begin() as conn:
        await conn.begin_nested()
        yield
        await conn.rollback()

@pytest.fixture
def client() -> TestClient:
    return TestClient(app)

@pytest.fixture
def authorized_client(client: TestClient, db_session: Session) -> TestClient:
    # Create test user
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "Testpassword123#",
        "confirm_password": "Testpassword123#"
    }
    response = client.post(f"{settings.API_V1_STR}/users", json=user_data)
    print("***",response.json())
    assert response.status_code == 201
    
    # Login
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login", json=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Add token to client headers
    client.headers["Authorization"] = f"Bearer {token}"
    return client