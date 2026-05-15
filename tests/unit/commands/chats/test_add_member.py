from datetime import datetime, UTC
from uuid import uuid4

import pytest

from app.application.commands.chats.add_member import AddMemberCommand, AddMemberHandler
from app.domain.entities.user import User, UserSettings
from app.domain.entities.chat import Chat, ChatMember
from app.domain.entities.enums import ChatType, ChatRole
from app.domain.exceptions import NotFoundError, ForbiddenError, AlreadyExistsError
from tests.unit.fake_repos import FakeUserRepository, FakeChatRepository, FakeChatMemberRepository


@pytest.fixture
def actor():
    return User(
        id=uuid4(),
        phone_number="+79001234567",
        display_name="Иван Иванов",
        created_at=datetime.now(UTC),
        settings=UserSettings(),
    )


@pytest.fixture
def new_user():
    return User(
        id=uuid4(),
        phone_number="+79007654321",
        display_name="Пётр Петров",
        created_at=datetime.now(UTC),
        settings=UserSettings(),
    )


@pytest.fixture
def group_chat(actor):
    return Chat(
        id=uuid4(),
        type=ChatType.GROUP,
        created_by=actor.id,
        created_at=datetime.now(UTC),
        title="Тестовая группа",
    )


@pytest.fixture
async def fake_repos(actor, new_user, group_chat):
    user_repo = FakeUserRepository()
    chat_repo = FakeChatRepository()
    chat_member_repo = FakeChatMemberRepository()

    await user_repo.save(actor)
    await user_repo.save(new_user)

    group_chat.add_member()
    await chat_repo.save(group_chat)

    await chat_member_repo.save(ChatMember(
        id=uuid4(),
        chat_id=group_chat.id,
        user_id=actor.id,
        joined_at=datetime.now(UTC),
        role=ChatRole.OWNER,
    ))

    return user_repo, chat_repo, chat_member_repo


@pytest.mark.asyncio
async def test_add_member_success(fake_repos, actor, new_user, group_chat):
    """Успешное добавление участника в группу"""
    user_repo, chat_repo, chat_member_repo = fake_repos
    handler = AddMemberHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
        user_repo=user_repo,
    )

    cmd = AddMemberCommand(
        actor_id=actor.id,
        chat_id=group_chat.id,
        user_id=new_user.id,
    )
    member = await handler.handle(cmd)

    assert member.user_id == new_user.id
    assert member.chat_id == group_chat.id
    assert member.role == ChatRole.MEMBER


@pytest.mark.asyncio
async def test_add_member_increments_count(fake_repos, actor, new_user, group_chat):
    """После добавления счётчик участников увеличился"""
    user_repo, chat_repo, chat_member_repo = fake_repos
    handler = AddMemberHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
        user_repo=user_repo,
    )

    cmd = AddMemberCommand(
        actor_id=actor.id,
        chat_id=group_chat.id,
        user_id=new_user.id,
    )
    await handler.handle(cmd)

    chat = await chat_repo.get_by_id(group_chat.id)
    assert chat.member_count == 2


@pytest.mark.asyncio
async def test_add_member_chat_not_found(fake_repos, actor, new_user):
    """Чат не существует — NotFoundError"""
    user_repo, chat_repo, chat_member_repo = fake_repos
    handler = AddMemberHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
        user_repo=user_repo,
    )

    cmd = AddMemberCommand(
        actor_id=actor.id,
        chat_id=uuid4(),
        user_id=new_user.id,
    )

    with pytest.raises(NotFoundError):
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_add_member_user_not_found(fake_repos, actor, group_chat):
    """Добавляемый пользователь не существует — NotFoundError"""
    user_repo, chat_repo, chat_member_repo = fake_repos
    handler = AddMemberHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
        user_repo=user_repo,
    )

    cmd = AddMemberCommand(
        actor_id=actor.id,
        chat_id=group_chat.id,
        user_id=uuid4(),
    )

    with pytest.raises(NotFoundError):
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_add_member_actor_not_in_chat(fake_repos, new_user, group_chat):
    """Актор не состоит в чате — ForbiddenError"""
    user_repo, chat_repo, chat_member_repo = fake_repos
    handler = AddMemberHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
        user_repo=user_repo,
    )

    cmd = AddMemberCommand(
        actor_id=uuid4(),
        chat_id=group_chat.id,
        user_id=new_user.id,
    )

    with pytest.raises(ForbiddenError):
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_add_member_insufficient_role(fake_repos, actor, new_user, group_chat):
    """Актор является обычным участником — ForbiddenError"""
    user_repo, chat_repo, chat_member_repo = fake_repos

    # Меняем роль актора на MEMBER
    member = await chat_member_repo.get_member(actor.id, group_chat.id)
    member.change_role(ChatRole.MEMBER)
    await chat_member_repo.save(member)

    handler = AddMemberHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
        user_repo=user_repo,
    )

    cmd = AddMemberCommand(
        actor_id=actor.id,
        chat_id=group_chat.id,
        user_id=new_user.id,
    )

    with pytest.raises(ForbiddenError):
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_add_member_already_in_chat(fake_repos, actor, new_user, group_chat):
    """Пользователь уже состоит в чате — AlreadyExistsError"""
    user_repo, chat_repo, chat_member_repo = fake_repos
    handler = AddMemberHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
        user_repo=user_repo,
    )

    cmd = AddMemberCommand(
        actor_id=actor.id,
        chat_id=group_chat.id,
        user_id=new_user.id,
    )

    await handler.handle(cmd)

    with pytest.raises(AlreadyExistsError):
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_add_member_to_private_chat_forbidden(fake_repos, actor, new_user):
    """Нельзя добавить участника в приватный чат — ForbiddenError"""
    user_repo, chat_repo, chat_member_repo = fake_repos

    private_chat = Chat(
        id=uuid4(),
        type=ChatType.PRIVATE,
        created_by=actor.id,
        created_at=datetime.now(UTC),
    )
    await chat_repo.save(private_chat)
    await chat_member_repo.save(ChatMember(
        id=uuid4(),
        chat_id=private_chat.id,
        user_id=actor.id,
        joined_at=datetime.now(UTC),
        role=ChatRole.OWNER,
    ))

    handler = AddMemberHandler(
        chat_repo=chat_repo,
        chat_member_repo=chat_member_repo,
        user_repo=user_repo,
    )

    cmd = AddMemberCommand(
        actor_id=actor.id,
        chat_id=private_chat.id,
        user_id=new_user.id,
    )

    with pytest.raises(ForbiddenError):
        await handler.handle(cmd)