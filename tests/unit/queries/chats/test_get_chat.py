from datetime import datetime, UTC
from uuid import uuid4

import pytest

from app.application.queries.chats.get_chat import GetChatQuery, GetChatHandler
from app.domain.entities.chat import Chat, ChatMember
from app.domain.entities.enums import ChatType, ChatRole
from app.domain.exceptions import NotFoundError, ForbiddenError
from tests.unit.fake_repos import FakeChatRepository, FakeChatMemberRepository


@pytest.fixture
def actor_id():
    return uuid4()


@pytest.fixture
def fake_repos():
    return FakeChatRepository(), FakeChatMemberRepository()


async def _setup_chat(chat_repo, chat_member_repo, chat_type, actor_id, is_public=False, add_actor=True):
    chat = Chat(
        id=uuid4(),
        type=chat_type,
        created_by=actor_id,
        created_at=datetime.now(UTC),
        title="Тестовый чат",
        is_public=is_public,
    )
    await chat_repo.save(chat)
    if add_actor:
        await chat_member_repo.save(ChatMember(
            id=uuid4(),
            chat_id=chat.id,
            user_id=actor_id,
            joined_at=datetime.now(UTC),
            role=ChatRole.MEMBER,
        ))
    return chat


@pytest.mark.asyncio
async def test_get_private_chat_success(fake_repos, actor_id):
    """Участник может получить приватный чат"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.PRIVATE, actor_id)

    handler = GetChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    result = await handler.handle(GetChatQuery(actor_id=actor_id, chat_id=chat.id))

    assert result.id == chat.id
    assert result.type == ChatType.PRIVATE


@pytest.mark.asyncio
async def test_get_public_channel_without_membership(fake_repos, actor_id):
    """Публичный канал доступен без членства"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(
        chat_repo, chat_member_repo, ChatType.CHANNEL, actor_id,
        is_public=True, add_actor=False,
    )

    handler = GetChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    result = await handler.handle(GetChatQuery(actor_id=uuid4(), chat_id=chat.id))

    assert result.id == chat.id


@pytest.mark.asyncio
async def test_get_public_group_without_membership(fake_repos, actor_id):
    """Публичная группа доступна без членства"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(
        chat_repo, chat_member_repo, ChatType.GROUP, actor_id,
        is_public=True, add_actor=False,
    )

    handler = GetChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    result = await handler.handle(GetChatQuery(actor_id=uuid4(), chat_id=chat.id))

    assert result.id == chat.id


@pytest.mark.asyncio
async def test_get_private_channel_without_membership_forbidden(fake_repos, actor_id):
    """Приватный канал недоступен без членства — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(
        chat_repo, chat_member_repo, ChatType.CHANNEL, actor_id,
        is_public=False, add_actor=False,
    )

    handler = GetChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(GetChatQuery(actor_id=uuid4(), chat_id=chat.id))


@pytest.mark.asyncio
async def test_get_secret_chat_by_member(fake_repos, actor_id):
    """Участник может получить секретный чат"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.SECRET, actor_id)

    handler = GetChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    result = await handler.handle(GetChatQuery(actor_id=actor_id, chat_id=chat.id))

    assert result.id == chat.id


@pytest.mark.asyncio
async def test_get_secret_chat_by_non_member_forbidden(fake_repos, actor_id):
    """Не участник не может получить секретный чат — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(
        chat_repo, chat_member_repo, ChatType.SECRET, actor_id,
        add_actor=False,
    )

    handler = GetChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(GetChatQuery(actor_id=uuid4(), chat_id=chat.id))


@pytest.mark.asyncio
async def test_get_chat_not_found(fake_repos, actor_id):
    """Чат не существует — NotFoundError"""
    chat_repo, chat_member_repo = fake_repos
    handler = GetChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(NotFoundError):
        await handler.handle(GetChatQuery(actor_id=actor_id, chat_id=uuid4()))


@pytest.mark.asyncio
async def test_get_chat_returns_correct_data(fake_repos, actor_id):
    """Возвращаемый чат содержит корректные данные"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.GROUP, actor_id, is_public=True)

    handler = GetChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    result = await handler.handle(GetChatQuery(actor_id=actor_id, chat_id=chat.id))

    assert result.id == chat.id
    assert result.title == "Тестовый чат"
    assert result.created_by == actor_id