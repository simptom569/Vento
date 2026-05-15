from datetime import datetime, UTC
from uuid import uuid4

import pytest

from app.application.commands.chats.open_private_chat import OpenPrivateChatCommand, OpenPrivateChatHandler
from app.domain.entities.user import User, UserSettings
from app.domain.entities.enums import ChatType
from app.domain.exceptions import NotFoundError
from tests.unit.fake_repos import FakeUserRepository, FakeChatRepository, FakeChatMemberRepository


@pytest.fixture
def actor():
    return User(
        id=uuid4(),
        phone_number="+79001234567",
        display_name="Иван Иванов",
        created_at=datetime.now(UTC),
        settings=UserSettings(),
    )


@pytest.fixture
def other_user():
    return User(
        id=uuid4(),
        phone_number="+79007654321",
        display_name="Пётр Петров",
        created_at=datetime.now(UTC),
        settings=UserSettings(),
    )


@pytest.fixture
async def fake_repos(actor, other_user):
    chat_member_repo = FakeChatMemberRepository()
    chat_repo = FakeChatRepository(chat_member_repo=chat_member_repo)
    user_repo = FakeUserRepository()
    await user_repo.save(actor)
    await user_repo.save(other_user)
    return user_repo, chat_repo, chat_member_repo


@pytest.mark.asyncio
async def test_open_private_chat_success(fake_repos, actor, other_user):
    """Успешное создание нового приватного чата"""
    user_repo, chat_repo, chat_member_repo = fake_repos
    handler = OpenPrivateChatHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
        user_repo=user_repo,
    )

    cmd = OpenPrivateChatCommand(actor_id=actor.id, user_id=other_user.id)
    chat = await handler.handle(cmd)

    assert chat.type == ChatType.PRIVATE
    assert chat.created_by == actor.id
    assert chat.id is not None


@pytest.mark.asyncio
async def test_open_private_chat_creates_two_members(fake_repos, actor, other_user):
    """После создания оба участника добавлены в чат"""
    user_repo, chat_repo, chat_member_repo = fake_repos
    handler = OpenPrivateChatHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
        user_repo=user_repo,
    )

    cmd = OpenPrivateChatCommand(actor_id=actor.id, user_id=other_user.id)
    chat = await handler.handle(cmd)

    actor_member = await chat_member_repo.get_member(actor.id, chat.id)
    other_member = await chat_member_repo.get_member(other_user.id, chat.id)

    assert actor_member is not None
    assert other_member is not None


@pytest.mark.asyncio
async def test_open_private_chat_member_count(fake_repos, actor, other_user):
    """После создания счётчик участников равен 2"""
    user_repo, chat_repo, chat_member_repo = fake_repos
    handler = OpenPrivateChatHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
        user_repo=user_repo,
    )

    cmd = OpenPrivateChatCommand(actor_id=actor.id, user_id=other_user.id)
    chat = await handler.handle(cmd)

    assert chat.member_count == 2


@pytest.mark.asyncio
async def test_open_private_chat_returns_existing(fake_repos, actor, other_user):
    """Повторный вызов возвращает тот же чат, не создаёт новый"""
    user_repo, chat_repo, chat_member_repo = fake_repos
    handler = OpenPrivateChatHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
        user_repo=user_repo,
    )

    cmd = OpenPrivateChatCommand(actor_id=actor.id, user_id=other_user.id)
    chat1 = await handler.handle(cmd)
    chat2 = await handler.handle(cmd)

    assert chat1.id == chat2.id
    assert len(chat_repo.chats) == 1


@pytest.mark.asyncio
async def test_open_private_chat_restores_deleted_member(fake_repos, actor, other_user):
    """Если актор удалил чат у себя — при повторном открытии восстанавливается"""
    user_repo, chat_repo, chat_member_repo = fake_repos
    handler = OpenPrivateChatHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
        user_repo=user_repo,
    )

    cmd = OpenPrivateChatCommand(actor_id=actor.id, user_id=other_user.id)
    chat = await handler.handle(cmd)

    # Симулируем soft-delete
    member = await chat_member_repo.get_member(actor.id, chat.id)
    member.soft_delete(last_message_seq=5)
    await chat_member_repo.save(member)

    # Открываем снова
    await handler.handle(cmd)

    restored = await chat_member_repo.get_member(actor.id, chat.id)
    assert restored is not None
    assert restored.deleted_at is None


@pytest.mark.asyncio
async def test_open_private_chat_user_not_found(fake_repos, actor):
    """Если пользователь не найден — NotFoundError"""
    user_repo, chat_repo, chat_member_repo = fake_repos
    handler = OpenPrivateChatHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
        user_repo=user_repo,
    )

    cmd = OpenPrivateChatCommand(actor_id=actor.id, user_id=uuid4())

    with pytest.raises(NotFoundError):
        await handler.handle(cmd)