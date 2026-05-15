from datetime import datetime, UTC, timedelta
from uuid import uuid4

import pytest
from jose import jwt

from app.core.config import settings


REGISTER_PAYLOAD = {
    "phone_number": "+79001234567",
    "display_name": "Иван Иванов",
    "password": "secret123",
}


@pytest.mark.asyncio
async def test_register_success(client):
    """Успешная регистрация через HTTP"""
    response = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["phone_number"] == "+79001234567"
    assert data["display_name"] == "Иван Иванов"
    assert "id" in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_phone(client):
    """Повторная регистрация с тем же номером — 409"""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    response = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_phone(client):
    """Невалидный номер телефона - 422"""
    response = await client.post("/api/v1/auth/register", json={
        **REGISTER_PAYLOAD,
        "phone_number": "not-a-phone",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client):
    """Пароль меньше 8 символов - 422"""
    response = await client.post("/api/v1/auth/register", json={
        **REGISTER_PAYLOAD,
        "password": "123",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client):
    """Успешный логин - возвращает access и refresh токены"""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    
    response = await client.post("/api/v1/auth/login", json={
        "phone_number": "+79001234567",
        "password": "secret123",
        "device_id": "test-device-001"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Неверный пароль - 401"""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    
    response = await client.post("/api/v1/auth/login", json={
        "phone_number": "+79001234567",
        "password": "wrongpassword",
        "device_id": "test-device-001",
    })
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_phone(client):
    """Несуществующий номер - 401"""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    
    response = await client.post("/api/v1/auth/login", json={
        "phone_number": "+79000000000",
        "password": "secret123",
        "device_id": "test-device-001",
    })
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_success(client):
    """Успешный refresh - возвращает новые токены"""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    login_response = await client.post("/api/v1/auth/login", json={
        "phone_number": "+79001234567",
        "password": "secret123",
        "device_id": "test-device-001",
    })
    refresh_token = login_response.json()["refresh_token"]
    
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_refresh_invalid_token(client):
    """Невалидный refresh токен - 401"""
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": "fake-token",
    })
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_success(client):
    """Успешный logout - 204, после чего refresh токен не работае"""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    login_response = await client.post("/api/v1/auth/login", json={
        "phone_number": "+79001234567",
        "password": "secret123",
        "device_id": "test-device-001",
    })
    refresh_token = login_response.json()["refresh_token"]
    
    logout_response = await client.post("/api/v1/auth/logout", json={
        "refresh_token": refresh_token,
    })
    assert logout_response.status_code == 204
    
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_success(client):
    """Авторизованный запрос возвращается данные пользователя"""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    login_response = await client.post("/api/v1/auth/login", json={
        "phone_number": "+79001234567",
        "password": "secret123",
        "device_id": "test-device-001",
    })
    access_token = login_response.json()["access_token"]
    
    response = await client.get("/api/v1/users/me", headers={
        "Authorization": f"Bearer {access_token}",
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["phone_number"] == "+79001234567"
    assert data["display_name"] == "Иван Иванов"
    assert "id" in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_get_me_no_token(client):
    """Запрос без токена - 401 (заголовок обязателен)"""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client):
    """Невалидный токен - 401"""
    response = await client.get("/api/v1/users/me", headers={
        "Authorization": "Bearer invalid.token.here",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_expired_token(client):
    """Истекший токен - 401"""
    payload = {
        "sub": str(uuid4()),
        "exp": datetime.now(UTC) - timedelta(minutes=1),
        "type": "access",
    }
    expired_token = jwt.encode(payload, settings.JWT_PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM)
    
    response = await client.get("/api/v1/users/me", headers={
        "Authorization": f"Bearer {expired_token}",
    })
    assert response.status_code == 401