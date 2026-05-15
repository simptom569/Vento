from uuid import uuid4

import pytest

from app.application.commands.chats.create_group import CreateGroupCommand, CreateGroupHandler
from app.domain.entities.enums import ChatType, ChatRole
from tests.unit.fake_repos import FakeChatRepository, FakeChatMemberRepository


@pytest.fixture
def actor_id():
    return uuid4()


@pytest.fixture
def fake_repos():
    return FakeChatRepository(), FakeChatMemberRepository()


@pytest.mark.asyncio
async def test_create_group_success(fake_repos, actor_id):
    """Успешное создание группы"""
    chat_repo, chat_member_repo = fake_repos
    handler = CreateGroupHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = CreateGroupCommand(actor_id=actor_id, title="Моя группа")
    group = await handler.handle(cmd)

    assert group.type == ChatType.GROUP
    assert group.title == "Моя группа"
    assert group.created_by == actor_id
    assert group.id is not None


@pytest.mark.asyncio
async def test_create_group_owner_added(fake_repos, actor_id):
    """Создатель добавлен как OWNER"""
    chat_repo, chat_member_repo = fake_repos
    handler = CreateGroupHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = CreateGroupCommand(actor_id=actor_id, title="Моя группа")
    group = await handler.handle(cmd)

    member = await chat_member_repo.get_member(actor_id, group.id)
    assert member is not None
    assert member.role == ChatRole.OWNER


@pytest.mark.asyncio
async def test_create_group_member_count(fake_repos, actor_id):
    """После создания счётчик участников равен 1"""
    chat_repo, chat_member_repo = fake_repos
    handler = CreateGroupHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = CreateGroupCommand(actor_id=actor_id, title="Моя группа")
    group = await handler.handle(cmd)

    assert group.member_count == 1


@pytest.mark.asyncio
async def test_create_group_saved_to_repo(fake_repos, actor_id):
    """Группа сохранена в репозитории"""
    chat_repo, chat_member_repo = fake_repos
    handler = CreateGroupHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = CreateGroupCommand(actor_id=actor_id, title="Моя группа")
    group = await handler.handle(cmd)

    saved = await chat_repo.get_by_id(group.id)
    assert saved is not None
    assert saved.title == "Моя группа"


@pytest.mark.asyncio
async def test_create_group_with_avatar(fake_repos, actor_id):
    """Группа создаётся с аватаром"""
    chat_repo, chat_member_repo = fake_repos
    handler = CreateGroupHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = CreateGroupCommand(
        actor_id=actor_id,
        title="Моя группа",
        avatar_url="https://minio/avatars/group.png",
    )
    group = await handler.handle(cmd)

    assert group.avatar_url == "https://minio/avatars/group.png"


@pytest.mark.asyncio
async def test_create_group_not_public_by_default(fake_repos, actor_id):
    """По умолчанию группа приватная"""
    chat_repo, chat_member_repo = fake_repos
    handler = CreateGroupHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = CreateGroupCommand(actor_id=actor_id, title="Моя группа")
    group = await handler.handle(cmd)

    assert group.is_public is False