from datetime import datetime, UTC
from uuid import uuid4

import pytest

from app.application.commands.chats.change_member_role import ChangeMemberRoleCommand, ChangeMemberRoleHandler
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
def group_chat(actor_id):
    return Chat(
        id=uuid4(),
        type=ChatType.GROUP,
        created_by=actor_id,
        created_at=datetime.now(UTC),
        title="Тестовая группа",
    )


@pytest.fixture
async def fake_repos(actor_id, user_id, group_chat):
    chat_repo = FakeChatRepository()
    chat_member_repo = FakeChatMemberRepository()

    await chat_repo.save(group_chat)

    await chat_member_repo.save(ChatMember(
        id=uuid4(),
        chat_id=group_chat.id,
        user_id=actor_id,
        joined_at=datetime.now(UTC),
        role=ChatRole.OWNER,
    ))

    await chat_member_repo.save(ChatMember(
        id=uuid4(),
        chat_id=group_chat.id,
        user_id=user_id,
        joined_at=datetime.now(UTC),
        role=ChatRole.MEMBER,
    ))

    return chat_repo, chat_member_repo


@pytest.mark.asyncio
async def test_change_member_role_success(fake_repos, actor_id, user_id, group_chat):
    """Успешная смена роли участника"""
    chat_repo, chat_member_repo = fake_repos
    handler = ChangeMemberRoleHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = ChangeMemberRoleCommand(
        actor_id=actor_id,
        chat_id=group_chat.id,
        user_id=user_id,
        role=ChatRole.ADMIN,
    )
    member = await handler.handle(cmd)

    assert member.role == ChatRole.ADMIN


@pytest.mark.asyncio
async def test_change_member_role_saved(fake_repos, actor_id, user_id, group_chat):
    """Новая роль сохранилась в репозитории"""
    chat_repo, chat_member_repo = fake_repos
    handler = ChangeMemberRoleHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = ChangeMemberRoleCommand(
        actor_id=actor_id,
        chat_id=group_chat.id,
        user_id=user_id,
        role=ChatRole.ADMIN,
    )
    await handler.handle(cmd)

    saved = await chat_member_repo.get_member(user_id, group_chat.id)
    assert saved.role == ChatRole.ADMIN


@pytest.mark.asyncio
async def test_change_member_role_chat_not_found(fake_repos, actor_id, user_id):
    """Чат не существует — NotFoundError"""
    chat_repo, chat_member_repo = fake_repos
    handler = ChangeMemberRoleHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = ChangeMemberRoleCommand(
        actor_id=actor_id,
        chat_id=uuid4(),
        user_id=user_id,
        role=ChatRole.ADMIN,
    )

    with pytest.raises(NotFoundError):
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_change_member_role_actor_not_in_chat(fake_repos, user_id, group_chat):
    """Актор не состоит в чате — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos
    handler = ChangeMemberRoleHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = ChangeMemberRoleCommand(
        actor_id=uuid4(),
        chat_id=group_chat.id,
        user_id=user_id,
        role=ChatRole.ADMIN,
    )

    with pytest.raises(ForbiddenError):
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_change_member_role_insufficient_role(fake_repos, actor_id, user_id, group_chat):
    """Актор не является владельцем — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos

    # Меняем роль актора на ADMIN (не OWNER)
    actor_member = await chat_member_repo.get_member(actor_id, group_chat.id)
    actor_member.change_role(ChatRole.ADMIN)
    await chat_member_repo.save(actor_member)

    handler = ChangeMemberRoleHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = ChangeMemberRoleCommand(
        actor_id=actor_id,
        chat_id=group_chat.id,
        user_id=user_id,
        role=ChatRole.ADMIN,
    )

    with pytest.raises(ForbiddenError):
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_change_member_role_user_not_in_chat(fake_repos, actor_id, group_chat):
    """Целевой пользователь не состоит в чате — NotFoundError"""
    chat_repo, chat_member_repo = fake_repos
    handler = ChangeMemberRoleHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = ChangeMemberRoleCommand(
        actor_id=actor_id,
        chat_id=group_chat.id,
        user_id=uuid4(),
        role=ChatRole.ADMIN,
    )

    with pytest.raises(NotFoundError):
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_change_member_role_private_chat_forbidden(fake_repos, actor_id, user_id):
    """Нельзя менять роли в приватном чате — ForbiddenError"""
    chat_repo, chat_member_repo = fake_repos

    private_chat = Chat(
        id=uuid4(),
        type=ChatType.PRIVATE,
        created_by=actor_id,
        created_at=datetime.now(UTC),
    )
    await chat_repo.save(private_chat)
    await chat_member_repo.save(ChatMember(
        id=uuid4(),
        chat_id=private_chat.id,
        user_id=actor_id,
        joined_at=datetime.now(UTC),
        role=ChatRole.OWNER,
    ))

    handler = ChangeMemberRoleHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
    )

    cmd = ChangeMemberRoleCommand(
        actor_id=actor_id,
        chat_id=private_chat.id,
        user_id=user_id,
        role=ChatRole.ADMIN,
    )

    with pytest.raises(ForbiddenError):
        await handler.handle(cmd)