from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from dishka.integrations.fastapi import inject, FromDishka
from jose import JWTError

from app.core.security import decode_access_token
from app.domain.entities.user import User
from app.domain.ports.repositories.user_repo import AbstractUserRepository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

@inject
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repo: FromDishka[AbstractUserRepository],
) -> User:
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Неверный тип токена")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    
    user = await user_repo.get_by_id(UUID(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]