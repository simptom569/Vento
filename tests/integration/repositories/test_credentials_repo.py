from uuid import uuid4
from datetime import datetime, timezone, timedelta

import pytest

from app.domain.entities.user import User
from app.infrastructure.db.repositories.user_repo import UserRepository
from app.infrastructure.db.repositories.credentials_repo import CredentialsRepository


@pytest.fixture
def user_repo(db_session):
    return UserRepository(session=db_session)


@pytest.fixture
def credentials_repo(db_session):
    return CredentialsRepository(session=db_session)


@pytest.fixture
async def sample_user(user_repo) -> User:
    """Сохраненный пользователь"""
    user = User(
        id=uuid4(),
        phone_number="+79001234567",
        display_name="Иван Иванов",
        created_at=datetime.now(timezone.utc),
    )
    await user_repo.save(user)
    return user


def make_expires_at(days: int = 30) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=days)


@pytest.mark.asyncio
async def test_save_and_get_password_hash(credentials_repo, sample_user):
    """Сохранили хэш - получили обратно"""
    await credentials_repo.save_password(sample_user.id, "hashed_password")
    
    result = await credentials_repo.get_password_hash(sample_user.id)
    assert result == "hashed_password"


@pytest.mark.asyncio
async def test_get_password_hash_not_found(credentials_repo, sample_user):
    """Пользователь без пароля возвращает None"""
    result = await credentials_repo.get_password_hash(sample_user.id)
    assert result is None


@pytest.mark.asyncio
async def test_save_session_and_get_by_token_hash(credentials_repo, sample_user):
    """Сохранили сессию - нашли по хэшу токена"""
    family_id = uuid4()
    await credentials_repo.save_session(
        user_id=sample_user.id,
        device_id="device-001",
        refresh_token_hash="token_hash_abc",
        expires_at=make_expires_at(),
        family_id=family_id,
    )
    
    session = await credentials_repo.get_session_by_token_hash("token_hash_abc")
    assert session is not None
    assert session.user_id == sample_user.id
    assert session.device_id == "device-001"
    assert session.family_id == family_id


@pytest.mark.asyncio
async def test_get_session_by_token_hash_not_found(credentials_repo, sample_user):
    """Несуществующий хэш возвращает None"""
    result = await credentials_repo.get_session_by_token_hash("nonexistent_hash")
    assert result is None


@pytest.mark.asyncio
async def test_get_session_by_family(credentials_repo, sample_user):
    """Нашли сессию по family_id"""
    family_id = uuid4()
    await credentials_repo.save_session(
        user_id=sample_user.id,
        device_id="device-001",
        refresh_token_hash="token_hash_abc",
        expires_at=make_expires_at(),
        family_id=family_id,
    )
    
    session = await credentials_repo.get_session_by_family(family_id)
    assert session is not None
    assert session.family_id == family_id


@pytest.mark.asyncio
async def test_get_session_by_family_not_found(credentials_repo):
    """Несуществующая семья возвращает None"""
    result = await credentials_repo.get_session_by_family(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_upsert_session_creates_new(credentials_repo, sample_user):
    """Upsert создает сессию есть ее нет"""
    await credentials_repo.upsert_session(
        user_id=sample_user.id,
        device_id="device-001",
        refresh_token_hash="hash_1",
        expires_at=make_expires_at(),
        family_id=uuid4(),
    )
    
    session = await credentials_repo.get_session_by_token_hash("hash_1")
    assert session is not None


@pytest.mark.asyncio
async def test_upsert_session_updates_existing(credentials_repo, sample_user):
    """Повторный upsert для того же device_id обновляет сессию, не дублирует"""
    family_id = uuid4()
    await credentials_repo.upsert_session(
        user_id=sample_user.id,
        device_id="device-001",
        refresh_token_hash="hash_old",
        expires_at=make_expires_at(),
        family_id=family_id,
    )
    await credentials_repo.upsert_session(
        user_id=sample_user.id,
        device_id="device-001",
        refresh_token_hash="hash_new",
        expires_at=make_expires_at(),
        family_id=uuid4(),
    )
    
    # Старый токен не существует
    old_session = await credentials_repo.get_session_by_token_hash("hash_old")
    assert old_session is None
    
    # Новый токен есть
    new_session = await credentials_repo.get_session_by_token_hash("hash_new")
    assert new_session is not None
    assert new_session.device_id == "device-001"


@pytest.mark.asyncio
async def test_delete_session(credentials_repo, sample_user):
    """Удалили сессию по id - она не находится"""
    await credentials_repo.save_session(
        user_id=sample_user.id,
        device_id="device-001",
        refresh_token_hash="hash_abc",
        expires_at=make_expires_at(),
        family_id=uuid4(),
    )
    session = await credentials_repo.get_session_by_token_hash("hash_abc")
    assert session is not None
    
    await credentials_repo.delete_session(session.id)
    
    deleted = await credentials_repo.get_session_by_token_hash("hash_abc")
    assert deleted is None


@pytest.mark.asyncio
async def test_delete_sessions_by_family(credentials_repo, sample_user):
    """Удаление по family_id инвалидирует все сессии семьи"""
    family_id = uuid4()
    await credentials_repo.save_session(
        user_id=sample_user.id,
        device_id="device-001",
        refresh_token_hash="hash_1",
        expires_at=make_expires_at(),
        family_id=family_id,
    )
    await credentials_repo.save_session(
        user_id=sample_user.id,
        device_id="device-002",
        refresh_token_hash="hash_2",
        expires_at=make_expires_at(),
        family_id=family_id,
    )
    
    await credentials_repo.delete_sessions_by_family(family_id)
    
    assert await credentials_repo.get_session_by_token_hash("hash_1") is None
    assert await credentials_repo.get_session_by_token_hash("hash_2") is None


@pytest.mark.asyncio
async def test_delete_all_user_sessions(credentials_repo, sample_user):
    """Удаление всех сессий пользователя"""
    await credentials_repo.save_session(
        user_id=sample_user.id,
        device_id="device-001",
        refresh_token_hash="hash_1",
        expires_at=make_expires_at(),
        family_id=uuid4(),
    )
    await credentials_repo.save_session(
        user_id=sample_user.id,
        device_id="device-002",
        refresh_token_hash="hash_2",
        expires_at=make_expires_at(),
        family_id=uuid4(),
    )
    
    await credentials_repo.delete_all_user_sessions(sample_user.id)
    
    assert await credentials_repo.get_session_by_token_hash("hash_1") is None
    assert await credentials_repo.get_session_by_token_hash("hash_2") is None