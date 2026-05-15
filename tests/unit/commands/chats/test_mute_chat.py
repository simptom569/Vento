from datetime import datetime, UTC, timedelta
from uuid import uuid4

import pytest

from app.application.commands.chats.mute_chat import MuteChatCommand, MuteChatHandler
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


async def _setup_chat(chat_repo, chat_member_repo, chat_type, actor_id):
    chat = Chat(
        id=uuid4(),
        type=chat_type,
        created_by=actor_id,
        created_at=datetime.now(UTC),
        title="Тестовый чат",
    )
    await chat_repo.save(chat)
    await chat_member_repo.save(ChatMember(
        id=uuid4(),
        chat_id=chat.id,
        user_id=actor_id,
        joined_at=datetime.now(UTC),
        role=ChatRole.MEMBER,
    ))
    return chat


@pytest.mark.asyncio
async def test_mute_chat_success(fake_repos, actor_id):
    """Успешный мьют чата"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.GROUP, actor_id)

    mute_until = datetime.now(UTC) + timedelta(hours=8)
    handler = MuteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(MuteChatCommand(
        actor_id=actor_id,
        chat_id=chat.id,
        time=mute_until,
    ))

    member = await chat_member_repo.get_member(actor_id, chat.id)
    assert member.muted_until == mute_until


@pytest.mark.asyncio
async def test_mute_chat_saved(fake_repos, actor_id):
    """Мьют сохранён в репозитории"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.CHANNEL, actor_id)

    mute_until = datetime.now(UTC) + timedelta(days=1)
    handler = MuteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(MuteChatCommand(
        actor_id=actor_id,
        chat_id=chat.id,
        time=mute_until,
    ))

    saved = await chat_member_repo.get_member(actor_id, chat.id)
    assert saved.muted_until is not None


@pytest.mark.asyncio
async def test_mute_chat_not_found(fake_repos, actor_id):
    """Чат не существует — NotFoundError"""
    chat_repo, chat_member_repo = fake_repos
    handler = MuteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(NotFoundError):
        await handler.handle(MuteChatCommand(
            actor_id=actor_id,
            chat_id=uuid4(),
            time=datetime.now(UTC) + timedelta(hours=1),
        ))


@pytest.mark.asyncio
async def test_mute_chat_actor_not_in_chat(fake_repos, actor_id):
    """Актор не состоит в чате — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.GROUP, actor_id)

    handler = MuteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(MuteChatCommand(
            actor_id=uuid4(),
            chat_id=chat.id,
            time=datetime.now(UTC) + timedelta(hours=1),
        ))


@pytest.mark.asyncio
async def test_mute_private_chat(fake_repos, actor_id):
    """Мьют работает и для приватного чата"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.PRIVATE, actor_id)

    mute_until = datetime.now(UTC) + timedelta(hours=1)
    handler = MuteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(MuteChatCommand(
        actor_id=actor_id,
        chat_id=chat.id,
        time=mute_until,
    ))

    member = await chat_member_repo.get_member(actor_id, chat.id)
    assert member.muted_until == mute_until