from datetime import datetime, UTC
from uuid import uuid4

import pytest

from app.application.commands.chats.update_group import UpdateGroupCommand, UpdateGroupHandler
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


async def _setup_group(chat_repo, chat_member_repo, actor_id, actor_role=ChatRole.OWNER):
    group = Chat(
        id=uuid4(),
        type=ChatType.GROUP,
        created_by=actor_id,
        created_at=datetime.now(UTC),
        title="Старое название",
        avatar_url="https://minio/avatars/old.png",
    )
    await chat_repo.save(group)
    await chat_member_repo.save(ChatMember(
        id=uuid4(),
        chat_id=group.id,
        user_id=actor_id,
        joined_at=datetime.now(UTC),
        role=actor_role,
    ))
    return group


@pytest.mark.asyncio
async def test_update_group_title(fake_repos, actor_id):
    """Успешное обновление названия группы"""
    chat_repo, chat_member_repo = fake_repos
    group = await _setup_group(chat_repo, chat_member_repo, actor_id)

    handler = UpdateGroupHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(UpdateGroupCommand(
        actor_id=actor_id,
        chat_id=group.id,
        title="Новое название",
    ))

    saved = await chat_repo.get_by_id(group.id)
    assert saved.title == "Новое название"


@pytest.mark.asyncio
async def test_update_group_avatar(fake_repos, actor_id):
    """Успешное обновление аватара группы"""
    chat_repo, chat_member_repo = fake_repos
    group = await _setup_group(chat_repo, chat_member_repo, actor_id)

    handler = UpdateGroupHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(UpdateGroupCommand(
        actor_id=actor_id,
        chat_id=group.id,
        avatar_url="https://minio/avatars/new.png",
    ))

    saved = await chat_repo.get_by_id(group.id)
    assert saved.avatar_url == "https://minio/avatars/new.png"


@pytest.mark.asyncio
async def test_update_group_partial(fake_repos, actor_id):
    """Незаполненные поля не затирают старые значения"""
    chat_repo, chat_member_repo = fake_repos
    group = await _setup_group(chat_repo, chat_member_repo, actor_id)

    handler = UpdateGroupHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)
    await handler.handle(UpdateGroupCommand(
        actor_id=actor_id,
        chat_id=group.id,
        title="Новое название",
    ))

    saved = await chat_repo.get_by_id(group.id)
    assert saved.avatar_url == "https://minio/avatars/old.png"  # не затёрся
    assert saved.title == "Новое название"


@pytest.mark.asyncio
async def test_update_group_not_found(fake_repos, actor_id):
    """Группа не существует — NotFoundError"""
    chat_repo, chat_member_repo = fake_repos
    handler = UpdateGroupHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(NotFoundError):
        await handler.handle(UpdateGroupCommand(
            actor_id=actor_id,
            chat_id=uuid4(),
            title="Новое название",
        ))


@pytest.mark.asyncio
async def test_update_group_actor_not_in_chat(fake_repos, actor_id):
    """Актор не состоит в группе — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    group = await _setup_group(chat_repo, chat_member_repo, actor_id)

    handler = UpdateGroupHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(UpdateGroupCommand(
            actor_id=uuid4(),
            chat_id=group.id,
            title="Новое название",
        ))


@pytest.mark.asyncio
async def test_update_group_insufficient_role(fake_repos, actor_id):
    """Актор не является владельцем — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    group = await _setup_group(chat_repo, chat_member_repo, actor_id, actor_role=ChatRole.ADMIN)

    handler = UpdateGroupHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(UpdateGroupCommand(
            actor_id=actor_id,
            chat_id=group.id,
            title="Новое название",
        ))


@pytest.mark.asyncio
async def test_update_channel_as_group_forbidden(fake_repos, actor_id):
    """Нельзя обновить канал через UpdateGroupHandler — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos

    channel = Chat(
        id=uuid4(),
        type=ChatType.CHANNEL,
        created_by=actor_id,
        created_at=datetime.now(UTC),
        title="Канал",
    )
    await chat_repo.save(channel)
    await chat_member_repo.save(ChatMember(
        id=uuid4(),
        chat_id=channel.id,
        user_id=actor_id,
        joined_at=datetime.now(UTC),
        role=ChatRole.OWNER,
    ))

    handler = UpdateGroupHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    with pytest.raises(ForbiddenError):
        await handler.handle(UpdateGroupCommand(
            actor_id=actor_id,
            chat_id=channel.id,
            title="Новое название",
        ))