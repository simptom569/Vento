from datetime import datetime, UTC
from uuid import uuid4

import pytest

from app.application.commands.chats.leave_chat import LeaveChatCommand, LeaveChatHandler
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


async def _setup_chat(chat_repo, chat_member_repo, chat_type, actor_id, role=ChatRole.MEMBER):
    chat = Chat(
        id=uuid4(),
        type=chat_type,
        created_by=uuid4(),
        created_at=datetime.now(UTC),
        title="Тестовый чат",
        member_count=1,
    )
    await chat_repo.save(chat)
    await chat_member_repo.save(ChatMember(
        id=uuid4(),
        chat_id=chat.id,
        user_id=actor_id,
        joined_at=datetime.now(UTC),
        role=role,
    ))
    return chat


@pytest.mark.asyncio
async def test_leave_group_success(fake_repos, actor_id):
    """Успешный выход из группы"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.GROUP, actor_id)

    handler = LeaveChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(LeaveChatCommand(actor_id=actor_id, chat_id=chat.id))

    member = await chat_member_repo.get_member(actor_id, chat.id)
    assert member is None


@pytest.mark.asyncio
async def test_leave_channel_success(fake_repos, actor_id):
    """Успешный выход из канала"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.CHANNEL, actor_id)

    handler = LeaveChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(LeaveChatCommand(actor_id=actor_id, chat_id=chat.id))

    member = await chat_member_repo.get_member(actor_id, chat.id)
    assert member is None


@pytest.mark.asyncio
async def test_leave_chat_decrements_member_count(fake_repos, actor_id):
    """После выхода счётчик участников уменьшился"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.GROUP, actor_id)

    handler = LeaveChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(LeaveChatCommand(actor_id=actor_id, chat_id=chat.id))

    saved_chat = await chat_repo.get_by_id(chat.id)
    assert saved_chat.member_count == 0


@pytest.mark.asyncio
async def test_leave_private_chat_forbidden(fake_repos, actor_id):
    """Нельзя выйти из приватного чата — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.PRIVATE, actor_id)

    handler = LeaveChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(LeaveChatCommand(actor_id=actor_id, chat_id=chat.id))


@pytest.mark.asyncio
async def test_leave_secret_chat_forbidden(fake_repos, actor_id):
    """Нельзя выйти из секретного чата — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.SECRET, actor_id)

    handler = LeaveChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(LeaveChatCommand(actor_id=actor_id, chat_id=chat.id))


@pytest.mark.asyncio
async def test_leave_chat_not_found(fake_repos, actor_id):
    """Чат не существует — NotFoundError"""
    chat_repo, chat_member_repo = fake_repos
    handler = LeaveChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(NotFoundError):
        await handler.handle(LeaveChatCommand(actor_id=actor_id, chat_id=uuid4()))


@pytest.mark.asyncio
async def test_leave_chat_actor_not_in_chat(fake_repos, actor_id):
    """Актор не состоит в чате — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.GROUP, actor_id)

    handler = LeaveChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(LeaveChatCommand(actor_id=uuid4(), chat_id=chat.id))