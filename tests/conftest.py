from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.infrastructure.db.models.base import Base
from app.infrastructure.db.models.user import (
    UserModel,
    UserSettingsModel,
    UserContactModel,
    UserKeyModel,
    AuthSessionModel,
    UserCredentialModel,
)
from app.infrastructure.db.models.chat import (
    ChatModel,
    ChatMembersModel,
)
from app.core.config import settings


TEST_DATABASE_URL = settings.database_url.replace(
    f"/{settings.POSTGRES_DB}", "/vento_test"
)


@pytest.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session_factory(test_engine):
    return async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest.fixture
async def db_session(test_engine, test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session
        await session.rollback()