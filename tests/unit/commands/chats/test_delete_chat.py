from datetime import datetime, UTC
from uuid import uuid4

import pytest

from app.application.commands.chats.delete_chat import DeleteChatCommand, DeleteChatHandler
from app.domain.entities.chat import Chat, ChatMember
from app.domain.entities.enums import ChatType, ChatRole
from app.domain.exceptions import NotFoundError, ForbiddenError
from tests.unit.fake_repos import FakeChatRepository, FakeChatMemberRepository


@pytest.fixture
def actor_id():
    return uuid4()


@pytest.fixture
def other_user_id():
    return uuid4()


@pytest.fixture
def fake_repos():
    return FakeChatRepository(), FakeChatMemberRepository()


async def _setup_chat(chat_repo, chat_member_repo, chat_type, actor_id, other_user_id=None, actor_role=ChatRole.OWNER):
    """Хелпер — создаёт чат и добавляет участников"""
    chat = Chat(
        id=uuid4(),
        type=chat_type,
        created_by=actor_id,
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
        role=actor_role,
    ))
    if other_user_id:
        chat.add_member()
        await chat_repo.save(chat)
        await chat_member_repo.save(ChatMember(
            id=uuid4(),
            chat_id=chat.id,
            user_id=other_user_id,
            joined_at=datetime.now(UTC),
            role=ChatRole.MEMBER,
        ))
    return chat


# --- PRIVATE ---

@pytest.mark.asyncio
async def test_delete_private_chat_soft_delete(fake_repos, actor_id, other_user_id):
    """Удаление приватного чата у себя — soft delete"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.PRIVATE, actor_id, other_user_id)

    handler = DeleteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(DeleteChatCommand(actor_id=actor_id, chat_id=chat.id))

    member = await chat_member_repo.get_member(actor_id, chat.id)
    assert member is None  # get_member не возвращает deleted

    member_including_deleted = await chat_member_repo.get_member_including_deleted(actor_id, chat.id)
    assert member_including_deleted.deleted_at is not None


@pytest.mark.asyncio
async def test_delete_private_chat_for_everyone(fake_repos, actor_id, other_user_id):
    """Удаление приватного чата для всех — физическое удаление"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.PRIVATE, actor_id, other_user_id)

    handler = DeleteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(DeleteChatCommand(
        actor_id=actor_id,
        chat_id=chat.id,
        delete_for_everyone=True,
    ))

    assert await chat_repo.get_by_id(chat.id) is None


@pytest.mark.asyncio
async def test_delete_private_chat_other_member_intact(fake_repos, actor_id, other_user_id):
    """После soft delete у актора — второй участник всё ещё видит чат"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.PRIVATE, actor_id, other_user_id)

    handler = DeleteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(DeleteChatCommand(actor_id=actor_id, chat_id=chat.id))

    other_member = await chat_member_repo.get_member(other_user_id, chat.id)
    assert other_member is not None


# --- CHANNEL ---

@pytest.mark.asyncio
async def test_delete_channel_by_owner(fake_repos, actor_id):
    """Владелец удаляет канал — физическое удаление"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.CHANNEL, actor_id)

    handler = DeleteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(DeleteChatCommand(actor_id=actor_id, chat_id=chat.id))

    assert await chat_repo.get_by_id(chat.id) is None


@pytest.mark.asyncio
async def test_delete_channel_by_non_owner(fake_repos, actor_id):
    """Не владелец пытается удалить канал — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(
        chat_repo, chat_member_repo, ChatType.CHANNEL, actor_id,
        actor_role=ChatRole.ADMIN,
    )

    handler = DeleteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(DeleteChatCommand(actor_id=actor_id, chat_id=chat.id))


# --- GROUP ---

@pytest.mark.asyncio
async def test_delete_group_soft_delete(fake_repos, actor_id):
    """Удаление группы у себя — soft delete"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.GROUP, actor_id)

    handler = DeleteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(DeleteChatCommand(actor_id=actor_id, chat_id=chat.id))

    member_including_deleted = await chat_member_repo.get_member_including_deleted(actor_id, chat.id)
    assert member_including_deleted.deleted_at is not None


@pytest.mark.asyncio
async def test_delete_group_for_everyone_by_owner(fake_repos, actor_id):
    """Владелец удаляет группу для всех — физическое удаление"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.GROUP, actor_id)

    handler = DeleteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(DeleteChatCommand(
        actor_id=actor_id,
        chat_id=chat.id,
        delete_for_everyone=True,
    ))

    assert await chat_repo.get_by_id(chat.id) is None


@pytest.mark.asyncio
async def test_delete_group_for_everyone_by_non_owner(fake_repos, actor_id):
    """Не владелец пытается удалить группу для всех — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(
        chat_repo, chat_member_repo, ChatType.GROUP, actor_id,
        actor_role=ChatRole.ADMIN,
    )

    handler = DeleteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(DeleteChatCommand(
            actor_id=actor_id,
            chat_id=chat.id,
            delete_for_everyone=True,
        ))


# --- Общие ---

@pytest.mark.asyncio
async def test_delete_chat_not_found(fake_repos, actor_id):
    """Чат не существует — NotFoundError"""
    chat_repo, chat_member_repo = fake_repos
    handler = DeleteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(NotFoundError):
        await handler.handle(DeleteChatCommand(actor_id=actor_id, chat_id=uuid4()))


@pytest.mark.asyncio
async def test_delete_chat_actor_not_in_chat(fake_repos, actor_id):
    """Актор не состоит в чате — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.GROUP, actor_id)

    handler = DeleteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(DeleteChatCommand(actor_id=uuid4(), chat_id=chat.id))