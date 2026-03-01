from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from ..db import Base
from ..main import app, get_session


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Создай тестовый engine для тестовой БД в памяти"""
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(
        test_db_url,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_session_maker(test_engine):
    """Создай сессию для теста"""
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_database(test_engine):
    """Создай таблицы БД перед каждым тестом"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def override_get_session(test_session_maker):
    """Переопредели get_session для тестов"""

    async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_maker() as session:
            yield session

    return get_test_session


@pytest_asyncio.fixture
async def client(override_get_session):
    """Верни TestClient с переопределённой БД"""
    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
