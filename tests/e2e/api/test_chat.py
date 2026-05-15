import pytest
from httpx import AsyncClient


# --- Helpers ---

async def register_and_login(client: AsyncClient, phone: str) -> str:
    """Регистрация + логин, возвращает access_token"""
    await client.post("/api/v1/auth/register", json={
        "phone_number": phone,
        "display_name": "Test User",
        "password": "password123",
    })
    response = await client.post("/api/v1/auth/login", json={
        "phone_number": phone,
        "password": "password123",
        "device_id": "device-001",
    })
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- Fixtures ---

@pytest.fixture
async def token(client):
    return await register_and_login(client, "+79001234567")


@pytest.fixture
async def other_token(client):
    return await register_and_login(client, "+79009999999")


@pytest.fixture
async def third_token(client):
    return await register_and_login(client, "+79008888888")


async def get_my_user_id(client: AsyncClient, token: str) -> str:
    response = await client.get("/api/v1/users/me", headers=auth_headers(token))
    return response.json()["id"]


async def create_group(client: AsyncClient, token: str, title: str = "Тестовая группа", is_public: bool = False) -> dict:
    response = await client.post(
        "/api/v1/chats/group",
        json={"title": title, "is_public": is_public},
        headers=auth_headers(token),
    )
    return response.json()


async def create_channel(client: AsyncClient, token: str, title: str = "Тестовый канал", username: str | None = None, is_public: bool = False) -> dict:
    body = {"title": title, "is_public": is_public}
    if username:
        body["username"] = username
    response = await client.post(
        "/api/v1/chats/channel",
        json=body,
        headers=auth_headers(token),
    )
    return response.json()


# =============================================================================
# CREATE GROUP
# =============================================================================

@pytest.mark.asyncio
async def test_create_group(client, token):
    """Создали группу - вернулся 201 с данными"""
    response = await client.post(
        "/api/v1/chats/group",
        json={"title": "Тестовая группа"},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Тестовая группа"
    assert data["type"] == "GROUP"


@pytest.mark.asyncio
async def test_create_group_unauthorized(client):
    """Без токена - 401"""
    response = await client.post("/api/v1/chats/group", json={"title": "Группа"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_group_empty_title(client, token):
    """Пустое название - 422"""
    response = await client.post(
        "/api/v1/chats/group",
        json={"title": ""},
        headers=auth_headers(token),
    )
    assert response.status_code == 422


# =============================================================================
# CREATE CHANNEL
# =============================================================================

@pytest.mark.asyncio
async def test_create_channel(client, token):
    """Создали канал - вернулся 201"""
    response = await client.post(
        "/api/v1/chats/channel",
        json={"title": "Мой канал", "is_public": True},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "CHANNEL"
    assert data["is_public"] is True


@pytest.mark.asyncio
async def test_create_channel_duplicate_username(client, token):
    """Дублирующийся username канала - 409"""
    await create_channel(client, token, username="my_channel")
    response = await client.post(
        "/api/v1/chats/channel",
        json={"title": "Канал 2", "username": "my_channel"},
        headers=auth_headers(token),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_channel_unauthorized(client):
    """Без токена - 401"""
    response = await client.post("/api/v1/chats/channel", json={"title": "Канал"})
    assert response.status_code == 401


# =============================================================================
# OPEN PRIVATE CHAT
# =============================================================================

@pytest.mark.asyncio
async def test_open_private_chat(client, token, other_token):
    """Открыли личный чат с другим пользователем"""
    other_user_id = await get_my_user_id(client, other_token)

    response = await client.post(
        "/api/v1/chats/private",
        json={"user_id": other_user_id},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    assert response.json()["type"] == "PRIVATE"


@pytest.mark.asyncio
async def test_open_private_chat_twice_returns_same(client, token, other_token):
    """Повторное открытие личного чата возвращает тот же чат"""
    other_user_id = await get_my_user_id(client, other_token)

    first = await client.post(
        "/api/v1/chats/private",
        json={"user_id": other_user_id},
        headers=auth_headers(token),
    )
    second = await client.post(
        "/api/v1/chats/private",
        json={"user_id": other_user_id},
        headers=auth_headers(token),
    )
    assert first.json()["id"] == second.json()["id"]


@pytest.mark.asyncio
async def test_open_private_chat_user_not_found(client, token):
    """Несуществующий пользователь - 404"""
    response = await client.post(
        "/api/v1/chats/private",
        json={"user_id": "00000000-0000-0000-0000-000000000000"},
        headers=auth_headers(token),
    )
    assert response.status_code == 404


# =============================================================================
# GET USER CHATS
# =============================================================================

@pytest.mark.asyncio
async def test_get_user_chats(client, token):
    """Созданная группа появляется в списке чатов"""
    await create_group(client, token, title="Моя группа")

    response = await client.get("/api/v1/chats", headers=auth_headers(token))
    assert response.status_code == 200
    assert any(c["title"] == "Моя группа" for c in response.json())


@pytest.mark.asyncio
async def test_get_user_chats_empty(client, token):
    """Новый пользователь — пустой список"""
    response = await client.get("/api/v1/chats", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_user_chats_unauthorized(client):
    """Без токена - 401"""
    response = await client.get("/api/v1/chats")
    assert response.status_code == 401


# =============================================================================
# GET CHAT
# =============================================================================

@pytest.mark.asyncio
async def test_get_chat(client, token):
    """Получили чат по id"""
    chat = await create_group(client, token)
    chat_id = chat["id"]

    response = await client.get(f"/api/v1/chats/{chat_id}", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["id"] == chat_id


@pytest.mark.asyncio
async def test_get_chat_not_found(client, token):
    """Несуществующий chat_id - 404"""
    response = await client.get(
        "/api/v1/chats/00000000-0000-0000-0000-000000000000",
        headers=auth_headers(token),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_chat_forbidden(client, token, other_token):
    """Чужой приватный чат - 403"""
    chat = await create_group(client, token)
    chat_id = chat["id"]

    response = await client.get(f"/api/v1/chats/{chat_id}", headers=auth_headers(other_token))
    assert response.status_code == 403


# =============================================================================
# UPDATE GROUP
# =============================================================================

@pytest.mark.asyncio
async def test_update_group(client, token):
    """Обновили название группы"""
    chat = await create_group(client, token)
    chat_id = chat["id"]

    response = await client.patch(
        f"/api/v1/chats/{chat_id}/group",
        json={"title": "Новое название"},
        headers=auth_headers(token),
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_group_forbidden(client, token, other_token):
    """Не владелец не может обновить группу - 403"""
    chat = await create_group(client, token)
    chat_id = chat["id"]

    response = await client.patch(
        f"/api/v1/chats/{chat_id}/group",
        json={"title": "Взлом"},
        headers=auth_headers(other_token),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_group_empty_title(client, token):
    """Пустое название - 422"""
    chat = await create_group(client, token)
    chat_id = chat["id"]

    response = await client.patch(
        f"/api/v1/chats/{chat_id}/group",
        json={"title": ""},
        headers=auth_headers(token),
    )
    assert response.status_code == 422


# =============================================================================
# UPDATE CHANNEL
# =============================================================================

@pytest.mark.asyncio
async def test_update_channel(client, token):
    """Обновили название канала"""
    chat = await create_channel(client, token)
    chat_id = chat["id"]

    response = await client.patch(
        f"/api/v1/chats/{chat_id}/channel",
        json={"title": "Новое название канала"},
        headers=auth_headers(token),
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_channel_forbidden(client, token, other_token):
    """Не владелец не может обновить канал - 403"""
    chat = await create_channel(client, token)
    chat_id = chat["id"]

    response = await client.patch(
        f"/api/v1/chats/{chat_id}/channel",
        json={"title": "Взлом"},
        headers=auth_headers(other_token),
    )
    assert response.status_code == 403


# =============================================================================
# DELETE CHAT
# =============================================================================

@pytest.mark.asyncio
async def test_delete_chat(client, token):
    """Владелец удалил чат"""
    chat = await create_group(client, token)
    chat_id = chat["id"]
    
    response = await client.request(
        "DELETE",
        f"/api/v1/chats/{chat_id}",
        json={"deleted_for_everyone": True},
        headers=auth_headers(token),
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_chat_forbidden(client, token, other_token):
    """Не владелец не может удалить чат - 403"""
    chat = await create_group(client, token)
    chat_id = chat["id"]

    response = await client.request(
        "DELETE",
        f"/api/v1/chats/{chat_id}",
        json={"deleted_for_everyone": True},
        headers=auth_headers(other_token),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_chat_not_found(client, token):
    """Несуществующий чат - 404"""
    response = await client.request(
        "DELETE",
        "/api/v1/chats/00000000-0000-0000-0000-000000000000",
        json={"deleted_for_everyone": True},
        headers=auth_headers(token),
    )
    assert response.status_code == 404


# =============================================================================
# MUTE CHAT
# =============================================================================

@pytest.mark.asyncio
async def test_mute_chat(client, token):
    """Замьютили чат"""
    from datetime import datetime, timezone, timedelta
    chat = await create_group(client, token)
    chat_id = chat["id"]

    muted_until = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    response = await client.post(
        f"/api/v1/chats/{chat_id}/mute",
        json={"time": muted_until},
        headers=auth_headers(token),
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_mute_chat_not_found(client, token):
    """Несуществующий чат - 404"""
    from datetime import datetime, timezone, timedelta
    muted_until = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    response = await client.post(
        "/api/v1/chats/00000000-0000-0000-0000-000000000000/mute",
        json={"time": muted_until},
        headers=auth_headers(token),
    )
    assert response.status_code == 404


# =============================================================================
# JOIN / LEAVE
# =============================================================================

@pytest.mark.asyncio
async def test_join_chat(client, token, other_token):
    """Второй пользователь вступил в публичную группу"""
    chat = await create_group(client, token, is_public=True)
    chat_id = chat["id"]

    response = await client.post(f"/api/v1/chats/{chat_id}/join", headers=auth_headers(other_token))
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_join_chat_twice(client, token, other_token):
    """Повторный join - 409"""
    chat = await create_group(client, token, is_public=True)
    chat_id = chat["id"]

    await client.post(f"/api/v1/chats/{chat_id}/join", headers=auth_headers(other_token))
    response = await client.post(f"/api/v1/chats/{chat_id}/join", headers=auth_headers(other_token))
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_join_private_chat_forbidden(client, token, other_token):
    """Нельзя вступить в приватную группу - 403"""
    chat = await create_group(client, token, is_public=False)
    chat_id = chat["id"]

    response = await client.post(f"/api/v1/chats/{chat_id}/join", headers=auth_headers(other_token))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_leave_chat(client, token, other_token):
    """Пользователь вышел из группы"""
    chat = await create_group(client, token, is_public=True)
    chat_id = chat["id"]

    await client.post(f"/api/v1/chats/{chat_id}/join", headers=auth_headers(other_token))
    response = await client.post(f"/api/v1/chats/{chat_id}/leave", headers=auth_headers(other_token))
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_leave_chat_not_member(client, token, other_token):
    """Нельзя выйти из чата где не состоишь - 403"""
    chat = await create_group(client, token)
    chat_id = chat["id"]

    response = await client.post(f"/api/v1/chats/{chat_id}/leave", headers=auth_headers(other_token))
    assert response.status_code == 403


# =============================================================================
# MEMBERS
# =============================================================================

@pytest.mark.asyncio
async def test_get_chat_members(client, token):
    """Создатель группы есть в списке участников"""
    chat = await create_group(client, token)
    chat_id = chat["id"]

    response = await client.get(f"/api/v1/chats/{chat_id}/members", headers=auth_headers(token))
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_add_member(client, token, other_token):
    """Добавили участника в группу"""
    other_user_id = await get_my_user_id(client, other_token)
    chat = await create_group(client, token)
    chat_id = chat["id"]

    response = await client.post(
        f"/api/v1/chats/{chat_id}/members",
        json={"user_id": other_user_id},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    assert response.json()["user_id"] == other_user_id


@pytest.mark.asyncio
async def test_add_member_duplicate(client, token, other_token):
    """Добавить уже существующего участника - 409"""
    other_user_id = await get_my_user_id(client, other_token)
    chat = await create_group(client, token)
    chat_id = chat["id"]

    await client.post(
        f"/api/v1/chats/{chat_id}/members",
        json={"user_id": other_user_id},
        headers=auth_headers(token),
    )
    response = await client.post(
        f"/api/v1/chats/{chat_id}/members",
        json={"user_id": other_user_id},
        headers=auth_headers(token),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_add_member_forbidden(client, token, other_token, third_token):
    """Обычный участник не может добавлять людей - 403"""
    other_user_id = await get_my_user_id(client, other_token)
    third_user_id = await get_my_user_id(client, third_token)
    chat = await create_group(client, token, is_public=True)
    chat_id = chat["id"]

    # other вступает сам
    await client.post(f"/api/v1/chats/{chat_id}/join", headers=auth_headers(other_token))

    # other пытается добавить third — не должен
    response = await client.post(
        f"/api/v1/chats/{chat_id}/members",
        json={"user_id": third_user_id},
        headers=auth_headers(other_token),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_remove_member(client, token, other_token):
    """Владелец удалил участника"""
    other_user_id = await get_my_user_id(client, other_token)
    chat = await create_group(client, token)
    chat_id = chat["id"]

    await client.post(
        f"/api/v1/chats/{chat_id}/members",
        json={"user_id": other_user_id},
        headers=auth_headers(token),
    )
    response = await client.delete(
        f"/api/v1/chats/{chat_id}/members/{other_user_id}",
        headers=auth_headers(token),
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_remove_member_forbidden(client, token, other_token, third_token):
    """Обычный участник не может удалять других - 403"""
    third_user_id = await get_my_user_id(client, third_token)
    chat = await create_group(client, token, is_public=True)
    chat_id = chat["id"]

    await client.post(f"/api/v1/chats/{chat_id}/join", headers=auth_headers(other_token))
    await client.post(f"/api/v1/chats/{chat_id}/join", headers=auth_headers(third_token))

    response = await client.delete(
        f"/api/v1/chats/{chat_id}/members/{third_user_id}",
        headers=auth_headers(other_token),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_change_member_role(client, token, other_token):
    """Владелец повысил участника до админа"""
    other_user_id = await get_my_user_id(client, other_token)
    chat = await create_group(client, token)
    chat_id = chat["id"]

    await client.post(
        f"/api/v1/chats/{chat_id}/members",
        json={"user_id": other_user_id},
        headers=auth_headers(token),
    )
    response = await client.patch(
        f"/api/v1/chats/{chat_id}/members/{other_user_id}",
        json={"role": "ADMIN"},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_change_member_role_forbidden(client, token, other_token, third_token):
    """Обычный участник не может менять роли - 403"""
    third_user_id = await get_my_user_id(client, third_token)
    chat = await create_group(client, token, is_public=True)
    chat_id = chat["id"]

    await client.post(f"/api/v1/chats/{chat_id}/join", headers=auth_headers(other_token))
    await client.post(f"/api/v1/chats/{chat_id}/join", headers=auth_headers(third_token))

    response = await client.patch(
        f"/api/v1/chats/{chat_id}/members/{third_user_id}",
        json={"role": "ADMIN"},
        headers=auth_headers(other_token),
    )
    assert response.status_code == 403