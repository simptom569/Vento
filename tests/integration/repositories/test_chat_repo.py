from uuid import uuid4
from datetime import datetime, timezone

import pytest

from app.domain.entities.chat import Chat, ChatMember
from app.domain.entities.enums import ChatType, ChatRole
from app.domain.entities.user import User
from app.infrastructure.db.repositories.user_repo import UserRepository
from app.infrastructure.db.repositories.chat_repo import ChatRepository


@pytest.fixture
def user_repo(db_session):
    return UserRepository(session=db_session)


@pytest.fixture
def chat_repo(db_session):
    return ChatRepository(session=db_session)


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


def make_group_chat(created_by) -> Chat:
    return Chat(
        id=uuid4(),
        type=ChatType.GROUP,
        created_by=created_by,
        created_at=datetime.now(timezone.utc),
        title="Тестовая группа",
        is_public=True,
    )


def make_private_chat(created_by) -> Chat:
    return Chat(
        id=uuid4(),
        type=ChatType.PRIVATE,
        created_by=created_by,
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_save_and_get_by_id(chat_repo, sample_user):
    """Сохранили чат - нашли по id"""
    chat = make_group_chat(sample_user.id)
    await chat_repo.save(chat)

    found = await chat_repo.get_by_id(chat.id)

    assert found is not None
    assert found.id == chat.id
    assert found.title == "Тестовая группа"


@pytest.mark.asyncio
async def test_get_by_id_not_found(chat_repo):
    """Несуществующий id возвращает None"""
    found = await chat_repo.get_by_id(uuid4())
    assert found is None


@pytest.mark.asyncio
async def test_get_by_ids(chat_repo, sample_user):
    """Получили несколько чатов по списку id"""
    chat1 = make_group_chat(sample_user.id)
    chat2 = make_group_chat(sample_user.id)
    await chat_repo.save(chat1)
    await chat_repo.save(chat2)

    found = await chat_repo.get_by_ids([chat1.id, chat2.id])

    assert len(found) == 2
    assert {c.id for c in found} == {chat1.id, chat2.id}


@pytest.mark.asyncio
async def test_get_by_username(chat_repo, sample_user):
    """Нашли чат по username"""
    chat = make_group_chat(sample_user.id)
    chat.username = "test_group"
    await chat_repo.save(chat)

    found = await chat_repo.get_by_username("test_group")

    assert found is not None
    assert found.username == "test_group"


@pytest.mark.asyncio
async def test_get_by_username_not_found(chat_repo):
    """Несуществующий username возвращает None"""
    found = await chat_repo.get_by_username("nonexistent")
    assert found is None


@pytest.mark.asyncio
async def test_save_updates_existing(chat_repo, sample_user):
    """Повторный save обновляет чат"""
    chat = make_group_chat(sample_user.id)
    await chat_repo.save(chat)

    chat.title = "Новое название"
    await chat_repo.save(chat)

    found = await chat_repo.get_by_id(chat.id)
    assert found.title == "Новое название"


@pytest.mark.asyncio
async def test_delete(chat_repo, sample_user):
    """После удаления чат не находится"""
    chat = make_group_chat(sample_user.id)
    await chat_repo.save(chat)

    await chat_repo.delete(chat.id)

    found = await chat_repo.get_by_id(chat.id)
    assert found is None


@pytest.mark.asyncio
async def test_search_by_title(chat_repo, sample_user):
    """Поиск по title без учёта регистра"""
    chat = make_group_chat(sample_user.id)
    chat.title = "Python разработчики"
    await chat_repo.save(chat)

    results = await chat_repo.search("python")

    assert any(c.title == "Python разработчики" for c in results)


@pytest.mark.asyncio
async def test_search_by_username(chat_repo, sample_user):
    """Поиск по username канала"""
    chat = make_group_chat(sample_user.id)
    chat.username = "python_devs"
    await chat_repo.save(chat)

    results = await chat_repo.search("python_devs")

    assert any(c.username == "python_devs" for c in results)


@pytest.mark.asyncio
async def test_search_returns_only_public(chat_repo, sample_user):
    """Поиск не возвращает приватные чаты"""
    private_chat = make_group_chat(sample_user.id)
    private_chat.title = "Секретная группа"
    private_chat.is_public = False
    await chat_repo.save(private_chat)

    results = await chat_repo.search("Секретная")

    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_private_chat(chat_repo, user_repo, sample_user, db_session):
    """Находим личный чат между двумя пользователями"""
    from app.infrastructure.db.repositories.chat_member_repo import ChatMemberRepository
    from app.infrastructure.db.models.chat import ChatMembersModel

    other_user = User(
        id=uuid4(),
        phone_number="+79009999999",
        display_name="Пётр Петров",
        created_at=datetime.now(timezone.utc),
    )
    await user_repo.save(other_user)

    chat = make_private_chat(sample_user.id)
    await chat_repo.save(chat)

    # Добавляем обоих участников напрямую через модель
    db_session.add(ChatMembersModel(
        id=uuid4(), chat_id=chat.id, user_id=sample_user.id,
        role=ChatRole.MEMBER, joined_at=datetime.now(timezone.utc),
    ))
    db_session.add(ChatMembersModel(
        id=uuid4(), chat_id=chat.id, user_id=other_user.id,
        role=ChatRole.MEMBER, joined_at=datetime.now(timezone.utc),
    ))
    await db_session.commit()

    found = await chat_repo.get_private_chat(sample_user.id, other_user.id)

    assert found is not None
    assert found.id == chat.id


@pytest.mark.asyncio
async def test_get_private_chat_not_found(chat_repo, sample_user):
    """Личный чат не найден если его нет"""
    found = await chat_repo.get_private_chat(sample_user.id, uuid4())
    assert found is None