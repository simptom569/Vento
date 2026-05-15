from uuid import uuid4
from datetime import datetime, timezone

import pytest

from app.domain.entities.user import User
from app.domain.entities.enums import PrivacyVisibility, TwoFAMethod
from app.infrastructure.db.repositories.user_repo import UserRepository


@pytest.fixture
def user_repo(db_session):
    return UserRepository(session=db_session)


@pytest.fixture
def sample_user() -> User:
    return User(
        id=uuid4(),
        phone_number="+79001234567",
        display_name="Иван Иванов",
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_save_and_get_by_id(user_repo, sample_user):
    """Сохранили юзера - нашли по id"""
    await user_repo.save(sample_user)
    
    found = await user_repo.get_by_id(sample_user.id)
    
    assert found is not None
    assert found.id == sample_user.id
    assert found.display_name == "Иван Иванов"


@pytest.mark.asyncio
async def test_get_by_phone(user_repo, sample_user):
    """Нашли юзера по номеру телефона"""
    await user_repo.save(sample_user)
    
    found = await user_repo.get_by_phone("+79001234567")
    
    assert found is not None
    assert found.phone_number == "+79001234567"


@pytest.mark.asyncio
async def test_get_by_phone_not_found(user_repo):
    """Несуществующий номер возвращает None"""
    found = await user_repo.get_by_phone("+79000000000")
    assert found is None


@pytest.mark.asyncio
async def test_save_updates_existing(user_repo, sample_user):
    """Повторный save обновляет юзера"""
    await user_repo.save(sample_user)

    sample_user.display_name = "Пётр Петров"
    await user_repo.save(sample_user)

    found = await user_repo.get_by_id(sample_user.id)
    assert found.display_name == "Пётр Петров"


@pytest.mark.asyncio
async def test_soft_delete(user_repo, sample_user):
    """После удаления юзер не находится"""
    await user_repo.save(sample_user)
    await user_repo.delete(sample_user.id)

    found = await user_repo.get_by_id(sample_user.id)
    assert found is None


@pytest.mark.asyncio
async def test_default_settings_saved(user_repo, sample_user):
    """Настройки сохраняются с дефолтными значениями"""
    await user_repo.save(sample_user)

    found = await user_repo.get_by_id(sample_user.id)
    assert found.settings.privacy_last_seen == PrivacyVisibility.EVERYONE
    assert found.settings.notification_enabled is True
    assert found.settings.two_fa_method == TwoFAMethod.NONE


@pytest.mark.asyncio
async def test_search_by_username(user_repo, sample_user):
    """Поиск по username работает без учёта регистра"""
    sample_user.username = "ivan_ivanov"
    await user_repo.save(sample_user)

    results = await user_repo.search("IVAN")
    assert any(u.username == "ivan_ivanov" for u in results)