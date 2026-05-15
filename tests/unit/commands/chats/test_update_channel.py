from datetime import datetime, UTC
from uuid import uuid4

import pytest

from app.application.commands.chats.update_channel import UpdateChannelCommand, UpdateChannelHandler
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


async def _setup_channel(chat_repo, chat_member_repo, actor_id, actor_role=ChatRole.OWNER):
    channel = Chat(
        id=uuid4(),
        type=ChatType.CHANNEL,
        created_by=actor_id,
        created_at=datetime.now(UTC),
        title="Старое название",
        username="old_username",
        is_public=False,
    )
    await chat_repo.save(channel)
    await chat_member_repo.save(ChatMember(
        id=uuid4(),
        chat_id=channel.id,
        user_id=actor_id,
        joined_at=datetime.now(UTC),
        role=actor_role,
    ))
    return channel


@pytest.mark.asyncio
async def test_update_channel_title(fake_repos, actor_id):
    """Успешное обновление названия канала"""
    chat_repo, chat_member_repo = fake_repos
    channel = await _setup_channel(chat_repo, chat_member_repo, actor_id)

    handler = UpdateChannelHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(UpdateChannelCommand(
        actor_id=actor_id,
        chat_id=channel.id,
        title="Новое название",
    ))

    saved = await chat_repo.get_by_id(channel.id)
    assert saved.title == "Новое название"


@pytest.mark.asyncio
async def test_update_channel_username(fake_repos, actor_id):
    """Успешное обновление username канала"""
    chat_repo, chat_member_repo = fake_repos
    channel = await _setup_channel(chat_repo, chat_member_repo, actor_id)

    handler = UpdateChannelHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(UpdateChannelCommand(
        actor_id=actor_id,
        chat_id=channel.id,
        username="new_username",
    ))

    saved = await chat_repo.get_by_id(channel.id)
    assert saved.username == "new_username"


@pytest.mark.asyncio
async def test_update_channel_is_public(fake_repos, actor_id):
    """Успешное изменение публичности канала"""
    chat_repo, chat_member_repo = fake_repos
    channel = await _setup_channel(chat_repo, chat_member_repo, actor_id)

    handler = UpdateChannelHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(UpdateChannelCommand(
        actor_id=actor_id,
        chat_id=channel.id,
        is_public=True,
    ))

    saved = await chat_repo.get_by_id(channel.id)
    assert saved.is_public is True


@pytest.mark.asyncio
async def test_update_channel_partial(fake_repos, actor_id):
    """Незаполненные поля не затирают старые значения"""
    chat_repo, chat_member_repo = fake_repos
    channel = await _setup_channel(chat_repo, chat_member_repo, actor_id)

    handler = UpdateChannelHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(UpdateChannelCommand(
        actor_id=actor_id,
        chat_id=channel.id,
        title="Новое название",
    ))

    saved = await chat_repo.get_by_id(channel.id)
    assert saved.username == "old_username"  # не затёрся
    assert saved.title == "Новое название"


@pytest.mark.asyncio
async def test_update_channel_not_found(fake_repos, actor_id):
    """Канал не существует — NotFoundError"""
    chat_repo, chat_member_repo = fake_repos
    handler = UpdateChannelHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(NotFoundError):
        await handler.handle(UpdateChannelCommand(
            actor_id=actor_id,
            chat_id=uuid4(),
            title="Новое название",
        ))


@pytest.mark.asyncio
async def test_update_channel_actor_not_in_chat(fake_repos, actor_id):
    """Актор не состоит в канале — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    channel = await _setup_channel(chat_repo, chat_member_repo, actor_id)

    handler = UpdateChannelHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(UpdateChannelCommand(
            actor_id=uuid4(),
            chat_id=channel.id,
            title="Новое название",
        ))


@pytest.mark.asyncio
async def test_update_channel_insufficient_role(fake_repos, actor_id):
    """Актор не является владельцем — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    channel = await _setup_channel(chat_repo, chat_member_repo, actor_id, actor_role=ChatRole.ADMIN)

    handler = UpdateChannelHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(UpdateChannelCommand(
            actor_id=actor_id,
            chat_id=channel.id,
            title="Новое название",
        ))


@pytest.mark.asyncio
async def test_update_group_as_channel_forbidden(fake_repos, actor_id):
    """Нельзя обновить группу через UpdateChannelHandler — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos

    group = Chat(
        id=uuid4(),
        type=ChatType.GROUP,
        created_by=actor_id,
        created_at=datetime.now(UTC),
        title="Группа",
    )
    await chat_repo.save(group)
    await chat_member_repo.save(ChatMember(
        id=uuid4(),
        chat_id=group.id,
        user_id=actor_id,
        joined_at=datetime.now(UTC),
        role=ChatRole.OWNER,
    ))

    handler = UpdateChannelHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(UpdateChannelCommand(
            actor_id=actor_id,
            chat_id=group.id,
            title="Новое название",
        ))