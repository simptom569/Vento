from uuid import uuid4

import pytest

from app.application.commands.chats.create_channel import CreateChannelCommand, CreateChannelHandler
from app.domain.entities.enums import ChatType, ChatRole
from app.domain.exceptions import AlreadyExistsError
from tests.unit.fake_repos import FakeChatRepository, FakeChatMemberRepository


@pytest.fixture
def actor_id():
    return uuid4()


@pytest.fixture
def fake_repos():
    return FakeChatRepository(), FakeChatMemberRepository()


@pytest.mark.asyncio
async def test_create_channel_success(fake_repos, actor_id):
    """Успешное создание канала"""
    chat_repo, chat_member_repo = fake_repos
    handler = CreateChannelHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = CreateChannelCommand(
        actor_id=actor_id,
        title="Мой канал",
        username="mychannel",
        is_public=True,
    )
    channel = await handler.handle(cmd)

    assert channel.type == ChatType.CHANNEL
    assert channel.title == "Мой канал"
    assert channel.username == "mychannel"
    assert channel.is_public is True
    assert channel.created_by == actor_id


@pytest.mark.asyncio
async def test_create_channel_owner_added(fake_repos, actor_id):
    """Создатель добавлен как OWNER"""
    chat_repo, chat_member_repo = fake_repos
    handler = CreateChannelHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = CreateChannelCommand(actor_id=actor_id, title="Мой канал")
    channel = await handler.handle(cmd)

    member = await chat_member_repo.get_member(actor_id, channel.id)
    assert member is not None
    assert member.role == ChatRole.OWNER


@pytest.mark.asyncio
async def test_create_channel_member_count(fake_repos, actor_id):
    """После создания счётчик участников равен 1"""
    chat_repo, chat_member_repo = fake_repos
    handler = CreateChannelHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = CreateChannelCommand(actor_id=actor_id, title="Мой канал")
    channel = await handler.handle(cmd)

    assert channel.member_count == 1


@pytest.mark.asyncio
async def test_create_channel_duplicate_username(fake_repos, actor_id):
    """Канал с таким username уже существует — AlreadyExistsError"""
    chat_repo, chat_member_repo = fake_repos
    handler = CreateChannelHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = CreateChannelCommand(actor_id=actor_id, title="Мой канал", username="mychannel")
    await handler.handle(cmd)

    with pytest.raises(AlreadyExistsError):
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_create_channel_without_username(fake_repos, actor_id):
    """Канал без username создаётся успешно"""
    chat_repo, chat_member_repo = fake_repos
    handler = CreateChannelHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = CreateChannelCommand(actor_id=actor_id, title="Мой канал")
    channel = await handler.handle(cmd)

    assert channel.username is None
    assert channel.id is not None


@pytest.mark.asyncio
async def test_create_channel_saved_to_repo(fake_repos, actor_id):
    """Канал сохранён в репозитории"""
    chat_repo, chat_member_repo = fake_repos
    handler = CreateChannelHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = CreateChannelCommand(actor_id=actor_id, title="Мой канал")
    channel = await handler.handle(cmd)

    saved = await chat_repo.get_by_id(channel.id)
    assert saved is not None
    assert saved.title == "Мой канал"


@pytest.mark.asyncio
async def test_create_channel_default_not_public(fake_repos, actor_id):
    """По умолчанию канал приватный"""
    chat_repo, chat_member_repo = fake_repos
    handler = CreateChannelHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = CreateChannelCommand(actor_id=actor_id, title="Мой канал")
    channel = await handler.handle(cmd)

    assert channel.is_public is False