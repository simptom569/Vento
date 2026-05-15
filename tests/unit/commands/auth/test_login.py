from datetime import datetime, UTC, timedelta
from uuid import uuid4

import pytest

from app.application.commands.auth.login import LoginCommand, LoginHandler
from app.domain.exceptions import ForbiddenError
from app.core.security import hash_password, hash_refresh_token
from app.domain.entities.user import User, UserSettings
from tests.unit.fake_repos import FakeUserRepository, FakeCredentialsRepository


@pytest.fixture
def registered_user():
    """Пользователь с сохраненным паролем"""
    user = User(
        id=uuid4(),
        phone_number="+79001234567",
        display_name="Иван Иванов",
        created_at=datetime.now(UTC),
        settings=UserSettings(),
    )
    return user


@pytest.fixture
async def fake_repos(registered_user):
    user_repo = FakeUserRepository()
    credentials_repo = FakeCredentialsRepository()
    await user_repo.save(registered_user)
    await credentials_repo.save_password(registered_user.id, hash_password("secret123"))
    return user_repo, credentials_repo


@pytest.mark.asyncio
async def test_login_success(fake_repos):
    """Успешный логин - возвращает токены"""
    user_repo, credentials_repo = fake_repos
    handler = LoginHandler(user_repo=user_repo, credentials_repo=credentials_repo)
    
    cmd = LoginCommand(
        phone_number="+79001234567",
        password="secret123",
        device_id="device-001",
    )
    
    result = await handler.handle(cmd)
    
    assert result.access_token
    assert result.refresh_token
    assert result.user_id is not None


@pytest.mark.asyncio
async def test_login_wrong_password(fake_repos):
    """Неверный пароль - ForbiddenError"""
    user_repo, credentials_repo = fake_repos
    handler = LoginHandler(user_repo=user_repo, credentials_repo=credentials_repo)
    
    with pytest.raises(ForbiddenError):
        cmd = LoginCommand(
            phone_number="+79001234567",
            password="wrongpassword",
            device_id="device-001",
        )
        
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_login_wrong_phone(fake_repos):
    """Несуществующий номер - ForbiddenError(Не раскрываем что именно неверно)"""
    user_repo, credentials_repo = fake_repos
    handler = LoginHandler(user_repo=user_repo, credentials_repo=credentials_repo)
    
    with pytest.raises(ForbiddenError):
        cmd = LoginCommand(
            phone_number="+79000000000",
            password="secret123",
            device_id="device-001",
        )
        
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_login_creates_session(fake_repos):
    """После логина сессия сохранена в credentials_repo"""
    user_repo, credentials_repo = fake_repos
    handler = LoginHandler(user_repo=user_repo, credentials_repo=credentials_repo)
    
    cmd = LoginCommand(
        phone_number="+79001234567",
        password="secret123",
        device_id="device-001",
    )
    
    result = await handler.handle(cmd)
    
    session = await credentials_repo.get_session_by_token_hash(
        hash_refresh_token(result.refresh_token)
    )
    
    assert session is not None
    assert session.device_id == "device-001"


@pytest.mark.asyncio
async def test_login_same_device_upserts_session(fake_repos):
    """Повторный логин с того же устройства - не дублирует сессии"""
    user_repo, credentials_repo = fake_repos
    handler = LoginHandler(user_repo=user_repo, credentials_repo=credentials_repo)
    
    cmd = LoginCommand(
        phone_number="+79001234567",
        password="secret123",
        device_id="device-001",
    )
    
    await handler.handle(cmd)
    await handler.handle(cmd)
    
    sessions = [s for s in credentials_repo.sessions.values()
                if s.device_id == "device-001"]
    assert len(sessions) == 1