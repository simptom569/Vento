import pytest

from app.application.commands.auth.register import RegisterCommand, RegisterHandler
from app.domain.exceptions import AlreadyExistsError
from app.domain.entities.enums import PrivacyVisibility, TwoFAMethod
from tests.unit.fake_repos import FakeUserRepository, FakeCredentialsRepository


@pytest.fixture
def fake_repos():
    return FakeUserRepository(), FakeCredentialsRepository()


@pytest.mark.asyncio
async def test_register_success(fake_repos):
    """Успешная регистрация нового пользователя"""
    user_repo, credentials_repo = fake_repos
    handler = RegisterHandler(user_repo=user_repo, credentials_repo=credentials_repo)
    
    cmd = RegisterCommand(
        phone_number="+79001234567",
        display_name="Иван Иванов",
        password="secret123",
    )
    
    user = await handler.handle(cmd)
    
    assert user.phone_number == "+79001234567"
    assert user.display_name == "Иван Иванов"
    assert user.id is not None
    assert user.is_deleted is False
    assert user.settings is not None


@pytest.mark.asyncio
async def test_register_duplicate_phone(fake_repos):
    """Нельзя зарегестрироваться с уже существующим номером"""
    user_repo, credentials_repo = fake_repos
    handler = RegisterHandler(user_repo=user_repo, credentials_repo=credentials_repo)
    
    cmd = RegisterCommand(
        phone_number="+79001234567",
        display_name="Иван Иванов",
        password="secret123",
    )
    
    await handler.handle(cmd)
    
    with pytest.raises(AlreadyExistsError):
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_register_saves_to_repo(fake_repos):
    """После регистрации юзер сохранился"""
    user_repo, credentials_repo = fake_repos
    handler = RegisterHandler(user_repo=user_repo, credentials_repo=credentials_repo)
    
    cmd = RegisterCommand(
        phone_number="+79001234567",
        display_name="Иван Иванов",
        password="secret123",
    )
    
    await handler.handle(cmd)
    
    saved_user = await user_repo.get_by_phone("+79001234567")
    assert saved_user is not None
    assert saved_user.display_name == "Иван Иванов"


@pytest.mark.asyncio
async def test_register_saves_password(fake_repos):
    """Полсе регистрации хэш пароля соханен в credentials_repo"""
    user_repo, credentails_repo = fake_repos
    handler = RegisterHandler(user_repo=user_repo, credentials_repo=credentails_repo)
    
    cmd = RegisterCommand(
        phone_number="+79001234567",
        display_name="Иван Иванов",
        password="secret123",
    )
    
    user = await handler.handle(cmd)
    
    password_hash = await credentails_repo.get_password_hash(user.id)
    assert password_hash is not None
    assert password_hash != "secret123"


@pytest.mark.asyncio
async def test_register_default_settings(fake_repos):
    """При регистрации создаются дефолтные настройки"""
    user_repo, credentials_repo = fake_repos
    handler = RegisterHandler(user_repo=user_repo, credentials_repo=credentials_repo)
    
    cmd = RegisterCommand(
        phone_number="+79001234567",
        display_name="Иван Иванов",
        password="secret123",
    )
    
    user = await handler.handle(cmd)
    
    assert user.settings.notification_enabled is True
    assert user.settings.privacy_last_seen == PrivacyVisibility.EVERYONE
    assert user.settings.two_fa_method == TwoFAMethod.NONE