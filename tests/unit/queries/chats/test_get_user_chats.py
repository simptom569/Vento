from datetime import datetime, UTC
from uuid import uuid4

import pytest

from app.application.queries.chats.get_user_chats import GetUserChatsQuery, GetUserChatsHandler
from app.domain.entities.chat import Chat, ChatMember
from app.domain.entities.enums import ChatType, ChatRole
from tests.unit.fake_repos import FakeChatRepository, FakeChatMemberRepository


@pytest.fixture
def actor_id():
    return uuid4()


@pytest.fixture
def fake_repos():
    return FakeChatRepository(), FakeChatMemberRepository()


async def _create_chat(chat_repo, chat_member_repo, actor_id, chat_type=ChatType.GROUP):
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
async def test_get_user_chats_success(fake_repos, actor_id):
    """Успешное получение чатов пользователя"""
    chat_repo, chat_member_repo = fake_repos
    await _create_chat(chat_repo, chat_member_repo, actor_id)
    await _create_chat(chat_repo, chat_member_repo, actor_id)

    handler = GetUserChatsHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    chats = await handler.handle(GetUserChatsQuery(actor_id=actor_id))

    assert len(chats) == 2


@pytest.mark.asyncio
async def test_get_user_chats_empty(fake_repos, actor_id):
    """Пользователь не состоит ни в одном чате — пустой список"""
    chat_repo, chat_member_repo = fake_repos
    handler = GetUserChatsHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    chats = await handler.handle(GetUserChatsQuery(actor_id=actor_id))

    assert chats == []


@pytest.mark.asyncio
async def test_get_user_chats_only_own(fake_repos, actor_id):
    """Возвращаются только чаты актора, не чужие"""
    chat_repo, chat_member_repo = fake_repos
    await _create_chat(chat_repo, chat_member_repo, actor_id)

    # Чужой чат
    other_user_id = uuid4()
    await _create_chat(chat_repo, chat_member_repo, other_user_id)

    handler = GetUserChatsHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    chats = await handler.handle(GetUserChatsQuery(actor_id=actor_id))

    assert len(chats) == 1
    assert all(c.created_by == actor_id for c in chats)


@pytest.mark.asyncio
async def test_get_user_chats_different_types(fake_repos, actor_id):
    """Возвращаются чаты всех типов"""
    chat_repo, chat_member_repo = fake_repos
    await _create_chat(chat_repo, chat_member_repo, actor_id, ChatType.GROUP)
    await _create_chat(chat_repo, chat_member_repo, actor_id, ChatType.CHANNEL)
    await _create_chat(chat_repo, chat_member_repo, actor_id, ChatType.PRIVATE)

    handler = GetUserChatsHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    chats = await handler.handle(GetUserChatsQuery(actor_id=actor_id))

    assert len(chats) == 3
    types = {c.type for c in chats}
    assert ChatType.GROUP in types
    assert ChatType.CHANNEL in types
    assert ChatType.PRIVATE in types


@pytest.mark.asyncio
async def test_get_user_chats_excludes_soft_deleted(fake_repos, actor_id):
    """Soft-deleted чаты не возвращаются"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _create_chat(chat_repo, chat_member_repo, actor_id)

    # Симулируем soft-delete
    member = await chat_member_repo.get_member(actor_id, chat.id)
    member.soft_delete(last_message_seq=0)
    await chat_member_repo.save(member)

    handler = GetUserChatsHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    chats = await handler.handle(GetUserChatsQuery(actor_id=actor_id))

    assert len(chats) == 0


@pytest.mark.asyncio
async def test_get_user_chats_after_restore(fake_repos, actor_id):
    """После восстановления чат снова появляется в списке"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _create_chat(chat_repo, chat_member_repo, actor_id)

    # Soft-delete
    member = await chat_member_repo.get_member(actor_id, chat.id)
    member.soft_delete(last_message_seq=0)
    await chat_member_repo.save(member)

    # Восстанавливаем
    member.restore()
    await chat_member_repo.save(member)

    handler = GetUserChatsHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    chats = await handler.handle(GetUserChatsQuery(actor_id=actor_id))

    assert len(chats) == 1