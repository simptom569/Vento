from datetime import datetime, UTC, timedelta
from uuid import uuid4

import pytest

from app.application.commands.auth.refresh_token import RefreshTokenCommand, RefreshTokenHandler
from app.domain.exceptions import ForbiddenError, TokenTheftError
from app.domain.entities.session import AuthSession
from app.core.security import hash_refresh_token, generate_refresh_token
from tests.unit.fake_repos import FakeCredentialsRepository


def make_session(device_id="device-001", expires_delta=timedelta(days=30)) -> tuple[str, AuthSession]:
    """Хэлпер - создает сырой токен + сессию"""
    raw_token = generate_refresh_token()
    token_hash = hash_refresh_token(raw_token)
    session = AuthSession(
        id=uuid4(),
        user_id=uuid4(),
        device_id=device_id,
        family_id=uuid4(),
        expires_at=datetime.now(UTC) + expires_delta,
    )
    return raw_token, token_hash, session


@pytest.mark.asyncio
async def test_refresh_success():
    """Успешная ротация - возвращает новые токены"""
    credentials_repo = FakeCredentialsRepository()
    raw_token, token_hash, session = make_session()
    credentials_repo.sessions[token_hash] = session
    
    handler = RefreshTokenHandler(credentials_repo=credentials_repo)
    
    cmd = RefreshTokenCommand(
        refresh_token=raw_token,
    )
    
    result = await handler.handle(cmd)
    
    assert result.access_token
    assert result.refresh_token
    assert result.refresh_token != raw_token


@pytest.mark.asyncio
async def test_refresh_old_token_invalidated():
    """После ротации старый токен больше не работает"""
    credentials_repo = FakeCredentialsRepository()
    raw_token, token_hash, session = make_session()
    credentials_repo.sessions[token_hash] = session
    
    handler = RefreshTokenHandler(credentials_repo=credentials_repo)
    
    cmd = RefreshTokenCommand(
        refresh_token=raw_token,
    )
    
    await handler.handle(cmd)
    
    with pytest.raises(ForbiddenError):
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_refresh_expired_token():
    """Истекший токен - ForbiddenError"""
    credentials_repo = FakeCredentialsRepository()
    raw_token, token_hash, session = make_session(expires_delta=timedelta(days=-1))
    credentials_repo.sessions[token_hash] = session
    
    handler = RefreshTokenHandler(credentials_repo=credentials_repo)
    
    with pytest.raises(ForbiddenError):
        cmd = RefreshTokenCommand(
            refresh_token=raw_token,
        )
        
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_refresh_theft_detected():
    """
    Повторное использование старого токена при наличии активной сессии
    в той же семье -> TokenTheftError, все сессии семьи удалены
    """
    credentials_repo = FakeCredentialsRepository()
    raw_token, token_hash, session = make_session()
    family_id = session.family_id
    credentials_repo.sessions[token_hash] = session
    
    handler = RefreshTokenHandler(credentials_repo=credentials_repo)
    
    cmd = RefreshTokenCommand(
        refresh_token=raw_token,
    )
    
    await handler.handle(cmd)
    
    credentials_repo.sessions[token_hash] = AuthSession(
        id=uuid4(),
        user_id=session.user_id,
        device_id=session.device_id,
        family_id=family_id,
        expires_at=session.expires_at,
    )
    
    with pytest.raises(TokenTheftError):
        await handler.handle(cmd)
    
    remaining = [s for s in credentials_repo.sessions.values() if s.family_id == family_id]
    assert len(remaining) == 0