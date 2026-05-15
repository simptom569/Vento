from datetime import datetime, UTC
from uuid import uuid4

import pytest

from app.application.commands.chats.join_chat import JoinChatCommand, JoinChatHandler
from app.domain.entities.chat import Chat
from app.domain.entities.enums import ChatType, ChatRole
from app.domain.exceptions import NotFoundError, ForbiddenError, AlreadyExistsError
from tests.unit.fake_repos import FakeChatRepository, FakeChatMemberRepository


@pytest.fixture
def actor_id():
    return uuid4()


@pytest.fixture
def fake_repos():
    return FakeChatRepository(), FakeChatMemberRepository()


async def _setup_chat(chat_repo, chat_type, is_public=True):
    chat = Chat(
        id=uuid4(),
        type=chat_type,
        created_by=uuid4(),
        created_at=datetime.now(UTC),
        title="Тестовый чат",
        is_public=is_public,
    )
    await chat_repo.save(chat)
    return chat


@pytest.mark.asyncio
async def test_join_chat_success(fake_repos, actor_id):
    """Успешное вступление в публичный чат"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, ChatType.GROUP)

    handler = JoinChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    member = await handler.handle(JoinChatCommand(actor_id=actor_id, chat_id=chat.id))

    assert member.user_id == actor_id
    assert member.chat_id == chat.id


@pytest.mark.asyncio
async def test_join_chat_increments_member_count(fake_repos, actor_id):
    """После вступления счётчик участников увеличился"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, ChatType.GROUP)

    handler = JoinChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(JoinChatCommand(actor_id=actor_id, chat_id=chat.id))

    saved_chat = await chat_repo.get_by_id(chat.id)
    assert saved_chat.member_count == 1


@pytest.mark.asyncio
async def test_join_chat_member_saved(fake_repos, actor_id):
    """После вступления участник сохранён в репозитории"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, ChatType.GROUP)

    handler = JoinChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(JoinChatCommand(actor_id=actor_id, chat_id=chat.id))

    member = await chat_member_repo.get_member(actor_id, chat.id)
    assert member is not None


@pytest.mark.asyncio
async def test_join_chat_subscriber_role(fake_repos, actor_id):
    """Вступивший получает роль SUBSCRIBER"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, ChatType.CHANNEL)

    handler = JoinChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    member = await handler.handle(JoinChatCommand(actor_id=actor_id, chat_id=chat.id))

    assert member.role == ChatRole.SUBSCRIBER


@pytest.mark.asyncio
async def test_join_chat_not_found(fake_repos, actor_id):
    """Чат не существует — NotFoundError"""
    chat_repo, chat_member_repo = fake_repos
    handler = JoinChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(NotFoundError):
        await handler.handle(JoinChatCommand(actor_id=actor_id, chat_id=uuid4()))


@pytest.mark.asyncio
async def test_join_private_chat_forbidden(fake_repos, actor_id):
    """Нельзя вступить в приватный чат — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, ChatType.GROUP, is_public=False)

    handler = JoinChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(JoinChatCommand(actor_id=actor_id, chat_id=chat.id))


@pytest.mark.asyncio
async def test_join_private_type_forbidden(fake_repos, actor_id):
    """Нельзя вступить в чат типа PRIVATE — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, ChatType.PRIVATE, is_public=False)

    handler = JoinChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(JoinChatCommand(actor_id=actor_id, chat_id=chat.id))


@pytest.mark.asyncio
async def test_join_secret_type_forbidden(fake_repos, actor_id):
    """Нельзя вступить в SECRET чат — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, ChatType.SECRET, is_public=False)

    handler = JoinChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(JoinChatCommand(actor_id=actor_id, chat_id=chat.id))


@pytest.mark.asyncio
async def test_join_chat_already_member(fake_repos, actor_id):
    """Пользователь уже состоит в чате — AlreadyExistsError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, ChatType.GROUP)

    handler = JoinChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(JoinChatCommand(actor_id=actor_id, chat_id=chat.id))

    with pytest.raises(AlreadyExistsError):
        await handler.handle(JoinChatCommand(actor_id=actor_id, chat_id=chat.id))