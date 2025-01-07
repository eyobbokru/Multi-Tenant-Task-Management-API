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
from app.db.session import get_db

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:changeme@db:5432/test_taskmanagement"

engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def create_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True, scope="function")
async def clean_tables():
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield

@pytest.fixture
async def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
async def authorized_client(client: TestClient) -> TestClient:
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "Testpassword123#",
        "confirm_password": "Testpassword123#"
    }
    response = client.post(f"{settings.API_V1_STR}/users", json=user_data)
    assert response.status_code == 201

    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = client.post(f"{settings.API_V1_STR}/users/login", json=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    client.headers["Authorization"] = f"Bearer {token}"
    return client