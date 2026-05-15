from datetime import datetime, UTC
from uuid import uuid4

import pytest

from app.application.queries.chats.get_chat_members import GetChatMembersQuery, GetChatMembersHandler
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


async def _setup_chat(chat_repo, chat_member_repo, chat_type, actor_id, actor_role=ChatRole.MEMBER, extra_members=0):
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
    # Добавляем дополнительных участников если нужно
    for _ in range(extra_members):
        chat.add_member()
        await chat_member_repo.save(ChatMember(
            id=uuid4(),
            chat_id=chat.id,
            user_id=uuid4(),
            joined_at=datetime.now(UTC),
            role=ChatRole.MEMBER,
        ))
    await chat_repo.save(chat)
    return chat


@pytest.mark.asyncio
async def test_get_group_members_success(fake_repos, actor_id):
    """Успешное получение участников группы"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.GROUP, actor_id, extra_members=2)

    handler = GetChatMembersHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    members = await handler.handle(GetChatMembersQuery(actor_id=actor_id, chat_id=chat.id))

    assert len(members) == 3


@pytest.mark.asyncio
async def test_get_channel_members_by_owner(fake_repos, actor_id):
    """Владелец канала может получить список участников"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(
        chat_repo, chat_member_repo, ChatType.CHANNEL, actor_id,
        actor_role=ChatRole.OWNER, extra_members=1,
    )

    handler = GetChatMembersHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    members = await handler.handle(GetChatMembersQuery(actor_id=actor_id, chat_id=chat.id))

    assert len(members) == 2


@pytest.mark.asyncio
async def test_get_channel_members_by_admin(fake_repos, actor_id):
    """Админ канала может получить список участников"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(
        chat_repo, chat_member_repo, ChatType.CHANNEL, actor_id,
        actor_role=ChatRole.ADMIN,
    )

    handler = GetChatMembersHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    members = await handler.handle(GetChatMembersQuery(actor_id=actor_id, chat_id=chat.id))

    assert len(members) == 1


@pytest.mark.asyncio
async def test_get_channel_members_by_subscriber_forbidden(fake_repos, actor_id):
    """Подписчик не может получить список участников канала — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(
        chat_repo, chat_member_repo, ChatType.CHANNEL, actor_id,
        actor_role=ChatRole.SUBSCRIBER,
    )

    handler = GetChatMembersHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(GetChatMembersQuery(actor_id=actor_id, chat_id=chat.id))


@pytest.mark.asyncio
async def test_get_private_chat_members_forbidden(fake_repos, actor_id):
    """Нельзя получить участников приватного чата — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.PRIVATE, actor_id)

    handler = GetChatMembersHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(GetChatMembersQuery(actor_id=actor_id, chat_id=chat.id))


@pytest.mark.asyncio
async def test_get_secret_chat_members_forbidden(fake_repos, actor_id):
    """Нельзя получить участников секретного чата — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.SECRET, actor_id)

    handler = GetChatMembersHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(GetChatMembersQuery(actor_id=actor_id, chat_id=chat.id))


@pytest.mark.asyncio
async def test_get_chat_members_chat_not_found(fake_repos, actor_id):
    """Чат не существует — NotFoundError"""
    chat_repo, chat_member_repo = fake_repos
    handler = GetChatMembersHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(NotFoundError):
        await handler.handle(GetChatMembersQuery(actor_id=actor_id, chat_id=uuid4()))


@pytest.mark.asyncio
async def test_get_chat_members_actor_not_in_chat(fake_repos, actor_id):
    """Актор не состоит в чате — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.GROUP, actor_id)

    handler = GetChatMembersHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(GetChatMembersQuery(actor_id=uuid4(), chat_id=chat.id))