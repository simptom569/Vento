from uuid import uuid4
from datetime import datetime, timezone

import pytest

from app.domain.entities.chat import Chat, ChatMember
from app.domain.entities.enums import ChatType, ChatRole
from app.domain.entities.user import User
from app.infrastructure.db.repositories.user_repo import UserRepository
from app.infrastructure.db.repositories.chat_repo import ChatRepository
from app.infrastructure.db.repositories.chat_member_repo import ChatMemberRepository


@pytest.fixture
def user_repo(db_session):
    return UserRepository(session=db_session)


@pytest.fixture
def chat_repo(db_session):
    return ChatRepository(session=db_session)


@pytest.fixture
def member_repo(db_session):
    return ChatMemberRepository(session=db_session)


@pytest.fixture
async def sample_user(user_repo) -> User:
    user = User(
        id=uuid4(),
        phone_number="+79001234567",
        display_name="Иван Иванов",
        created_at=datetime.now(timezone.utc),
    )
    await user_repo.save(user)
    return user


@pytest.fixture
async def sample_chat(chat_repo, sample_user) -> Chat:
    chat = Chat(
        id=uuid4(),
        type=ChatType.GROUP,
        created_by=sample_user.id,
        created_at=datetime.now(timezone.utc),
        title="Тестовая группа",
        is_public=True,
    )
    await chat_repo.save(chat)
    return chat


def make_member(user_id, chat_id) -> ChatMember:
    return ChatMember(
        id=uuid4(),
        chat_id=chat_id,
        user_id=user_id,
        role=ChatRole.MEMBER,
        joined_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_save_and_get_member(member_repo, sample_user, sample_chat):
    """Сохранили участника - нашли по user_id и chat_id"""
    member = make_member(sample_user.id, sample_chat.id)
    await member_repo.save(member)

    found = await member_repo.get_member(sample_user.id, sample_chat.id)

    assert found is not None
    assert found.user_id == sample_user.id
    assert found.chat_id == sample_chat.id


@pytest.mark.asyncio
async def test_get_member_not_found(member_repo, sample_user, sample_chat):
    """Участник не найден если его нет"""
    found = await member_repo.get_member(sample_user.id, sample_chat.id)
    assert found is None


@pytest.mark.asyncio
async def test_save_updates_existing(member_repo, sample_user, sample_chat):
    """Повторный save обновляет роль участника"""
    member = make_member(sample_user.id, sample_chat.id)
    await member_repo.save(member)

    member.role = ChatRole.ADMIN
    await member_repo.save(member)

    found = await member_repo.get_member(sample_user.id, sample_chat.id)
    assert found.role == ChatRole.ADMIN


@pytest.mark.asyncio
async def test_get_chat_members(member_repo, user_repo, sample_chat, sample_user):
    """Получили всех участников чата"""
    other_user = User(
        id=uuid4(),
        phone_number="+79009999999",
        display_name="Пётр Петров",
        created_at=datetime.now(timezone.utc),
    )
    await user_repo.save(other_user)

    await member_repo.save(make_member(sample_user.id, sample_chat.id))
    await member_repo.save(make_member(other_user.id, sample_chat.id))

    members = await member_repo.get_chat_members(sample_chat.id)

    assert len(members) == 2
    assert {m.user_id for m in members} == {sample_user.id, other_user.id}


@pytest.mark.asyncio
async def test_delete_member(member_repo, sample_user, sample_chat):
    """Удалили участника - он не находится"""
    member = make_member(sample_user.id, sample_chat.id)
    await member_repo.save(member)

    await member_repo.delete(sample_user.id, sample_chat.id)

    found = await member_repo.get_member(sample_user.id, sample_chat.id)
    assert found is None


@pytest.mark.asyncio
async def test_get_member_including_deleted(member_repo, sample_user, sample_chat):
    """Находим участника даже после soft delete"""
    from datetime import UTC
    member = make_member(sample_user.id, sample_chat.id)
    member.deleted_at = datetime.now(UTC)
    await member_repo.save(member)

    # get_member не находит
    active = await member_repo.get_member(sample_user.id, sample_chat.id)
    assert active is None

    # get_member_including_deleted находит
    deleted = await member_repo.get_member_including_deleted(sample_user.id, sample_chat.id)
    assert deleted is not None
    assert deleted.user_id == sample_user.id


@pytest.mark.asyncio
async def test_get_user_memberships(member_repo, chat_repo, sample_user, sample_chat):
    """Получили все активные чаты пользователя"""
    other_chat = Chat(
        id=uuid4(),
        type=ChatType.GROUP,
        created_by=sample_user.id,
        created_at=datetime.now(timezone.utc),
        title="Второй чат",
        is_public=True,
    )
    await chat_repo.save(other_chat)

    await member_repo.save(make_member(sample_user.id, sample_chat.id))
    await member_repo.save(make_member(sample_user.id, other_chat.id))

    memberships = await member_repo.get_user_memberships(sample_user.id)

    assert len(memberships) == 2
    assert {m.chat_id for m in memberships} == {sample_chat.id, other_chat.id}


@pytest.mark.asyncio
async def test_get_user_memberships_excludes_deleted(member_repo, sample_user, sample_chat):
    """Удалённые чаты не попадают в memberships"""
    from datetime import UTC
    member = make_member(sample_user.id, sample_chat.id)
    member.deleted_at = datetime.now(UTC)
    await member_repo.save(member)

    memberships = await member_repo.get_user_memberships(sample_user.id)

    assert len(memberships) == 0