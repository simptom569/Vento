from pydantic import BaseModel, field_validator
from uuid import UUID
import re


class RegisterRequest(BaseModel):
    phone_number: str
    display_name: str
    password: str
    
    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^\+?[1-9]\d{7,14}$", v):
            raise ValueError("Некорректный формат номера")
        return v
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        return v


class RegisterResponse(BaseModel):
    id: UUID
    phone_number: str
    display_name: str
    username: str | None
    
    @classmethod
    def from_domain(cls, user) -> "RegisterResponse":
        return cls(
            id=user.id,
            phone_number=user.phone_number,
            display_name=user.display_name,
            username=user.username,
        )


class LoginRequest(BaseModel):
    phone_number: str
    password: str
    device_id: str
    device_name: str | None = None
    platform: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str