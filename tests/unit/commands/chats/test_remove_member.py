from datetime import datetime, UTC
from uuid import uuid4

import pytest

from app.application.commands.chats.remove_member import RemoveMemberCommand, RemoveMemberHandler
from app.domain.entities.chat import Chat, ChatMember
from app.domain.entities.enums import ChatType, ChatRole
from app.domain.exceptions import NotFoundError, ForbiddenError
from tests.unit.fake_repos import FakeChatRepository, FakeChatMemberRepository


@pytest.fixture
def actor_id():
    return uuid4()


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def fake_repos():
    return FakeChatRepository(), FakeChatMemberRepository()


async def _setup_chat(chat_repo, chat_member_repo, chat_type, actor_id, user_id=None, actor_role=ChatRole.OWNER):
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
    if user_id:
        chat.add_member()
        await chat_repo.save(chat)
        await chat_member_repo.save(ChatMember(
            id=uuid4(),
            chat_id=chat.id,
            user_id=user_id,
            joined_at=datetime.now(UTC),
            role=ChatRole.MEMBER,
        ))
    return chat


@pytest.mark.asyncio
async def test_remove_member_from_group_success(fake_repos, actor_id, user_id):
    """Успешный кик участника из группы"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.GROUP, actor_id, user_id)

    handler = RemoveMemberHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(RemoveMemberCommand(
        actor_id=actor_id,
        chat_id=chat.id,
        user_id=user_id,
    ))

    member = await chat_member_repo.get_member(user_id, chat.id)
    assert member is None


@pytest.mark.asyncio
async def test_remove_member_from_channel_success(fake_repos, actor_id, user_id):
    """Успешный кик участника из канала"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.CHANNEL, actor_id, user_id)

    handler = RemoveMemberHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(RemoveMemberCommand(
        actor_id=actor_id,
        chat_id=chat.id,
        user_id=user_id,
    ))

    member = await chat_member_repo.get_member(user_id, chat.id)
    assert member is None


@pytest.mark.asyncio
async def test_remove_member_decrements_count(fake_repos, actor_id, user_id):
    """После кика счётчик участников уменьшился"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.GROUP, actor_id, user_id)

    handler = RemoveMemberHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(RemoveMemberCommand(
        actor_id=actor_id,
        chat_id=chat.id,
        user_id=user_id,
    ))

    saved_chat = await chat_repo.get_by_id(chat.id)
    assert saved_chat.member_count == 1


@pytest.mark.asyncio
async def test_remove_member_chat_not_found(fake_repos, actor_id, user_id):
    """Чат не существует — NotFoundError"""
    chat_repo, chat_member_repo = fake_repos
    handler = RemoveMemberHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(NotFoundError):
        await handler.handle(RemoveMemberCommand(
            actor_id=actor_id,
            chat_id=uuid4(),
            user_id=user_id,
        ))


@pytest.mark.asyncio
async def test_remove_member_actor_not_in_chat(fake_repos, actor_id, user_id):
    """Актор не состоит в чате — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.GROUP, actor_id, user_id)

    handler = RemoveMemberHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(RemoveMemberCommand(
            actor_id=uuid4(),
            chat_id=chat.id,
            user_id=user_id,
        ))


@pytest.mark.asyncio
async def test_remove_member_insufficient_role(fake_repos, actor_id, user_id):
    """Актор является обычным участником — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(
        chat_repo, chat_member_repo, ChatType.GROUP, actor_id, user_id,
        actor_role=ChatRole.MEMBER,
    )

    handler = RemoveMemberHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(RemoveMemberCommand(
            actor_id=actor_id,
            chat_id=chat.id,
            user_id=user_id,
        ))


@pytest.mark.asyncio
async def test_remove_member_user_not_in_chat(fake_repos, actor_id):
    """Кикаемый пользователь не состоит в чате — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.GROUP, actor_id)

    handler = RemoveMemberHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(RemoveMemberCommand(
            actor_id=actor_id,
            chat_id=chat.id,
            user_id=uuid4(),
        ))


@pytest.mark.asyncio
async def test_remove_member_from_private_chat_forbidden(fake_repos, actor_id, user_id):
    """Нельзя кикнуть из приватного чата — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    chat = await _setup_chat(chat_repo, chat_member_repo, ChatType.PRIVATE, actor_id, user_id)

    handler = RemoveMemberHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(RemoveMemberCommand(
            actor_id=actor_id,
            chat_id=chat.id,
            user_id=user_id,
        ))