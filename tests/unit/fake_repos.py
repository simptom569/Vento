from uuid import UUID, uuid4

from app.domain.entities.user import User
from app.domain.entities.chat import Chat, ChatMember
from app.domain.entities.enums import ChatType
from app.domain.ports.repositories.user_repo import AbstractUserRepository
from app.domain.ports.repositories.credentials_repo import AbstractCredentialsRepository
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository
from app.domain.entities.session import AuthSession


class FakeUserRepository(AbstractUserRepository):
    def __init__(self):
        self.users: dict[str, User] = {}
    
    async def get_by_phone(self, phone_number: str) -> User | None:
        return self.users.get(phone_number)
    
    async def get_by_id(self, user_id) -> User | None:
        for user in self.users.values():
            if user.id == user_id:
                return user
        return None
    
    async def get_by_username(self, username: str) -> User | None:
        return None
    
    async def save(self, user: User) -> User:
        self.users[user.phone_number] = user
        return User
    
    async def delete(self, user_id) -> None:
        pass
    
    async def search(self, query: str, limit: int = 10) -> list[User]:
        return []
    
    async def search_contacts(self, actor_id: UUID, query: str, limit: int = 10) -> list[User]:
        return []


class FakeCredentialsRepository(AbstractCredentialsRepository):
    def __init__(self):
        self.passwords: dict[str, str] = {}
        self.sessions: dict[str, AuthSession] = {}

    async def save_password(self, user_id, password_hash: str) -> None:
        self.passwords[str(user_id)] = password_hash

    async def get_password_hash(self, user_id) -> str | None:
        return self.passwords.get(str(user_id))

    async def upsert_session(
        self,
        user_id,
        device_id,
        refresh_token_hash,
        expires_at,
        family_id,
        device_name=None,
        platform=None,
        ip_address=None
    ) -> None:
        self.sessions = {
            k: v for k, v in self.sessions.items()
            if not (v.user_id == user_id and v.device_id == device_id)
        }
        self.sessions[refresh_token_hash] = AuthSession(
            id=uuid4(), user_id=user_id, device_id=device_id,
            family_id=family_id, expires_at=expires_at,
        )

    async def save_session(
        self,
        user_id,
        device_id,
        refresh_token_hash,
        expires_at,
        family_id,
        device_name=None,
        platform=None,
        ip_address=None
    ) -> None:
        self.sessions[refresh_token_hash] = AuthSession(
            id=uuid4(),
            user_id=user_id,
            device_id=device_id,
            family_id=family_id,
            expires_at=expires_at,
        )

    async def get_session_by_token_hash(self, token_hash: str) -> AuthSession | None:
        return self.sessions.get(token_hash)

    async def get_session_by_family(self, family_id) -> AuthSession | None:
        for s in self.sessions.values():
            if s.family_id == family_id:
                return s
        return None

    async def delete_session(self, session_id) -> None:
        self.sessions = {k: v for k, v in self.sessions.items() if v.id != session_id}

    async def delete_sessions_by_family(self, family_id) -> None:
        self.sessions = {k: v for k, v in self.sessions.items() if v.family_id != family_id}

    async def delete_all_user_sessions(self, user_id) -> None:
        self.sessions = {k: v for k, v in self.sessions.items() if v.user_id != user_id}


class FakeChatRepository(AbstractChatRepository):
    def __init__(self, chat_member_repo: "FakeChatMemberRepository | None" = None):
        self.chats: dict[UUID, Chat] = {}
        self._member_repo = chat_member_repo

    async def get_by_id(self, chat_id: UUID) -> Chat | None:
        return self.chats.get(chat_id)

    async def get_by_ids(self, chat_ids: list[UUID]) -> list[Chat]:
        return [self.chats[cid] for cid in chat_ids if cid in self.chats]

    async def get_by_username(self, username: str) -> Chat | None:
        for chat in self.chats.values():
            if chat.username == username:
                return chat
        return None

    async def save(self, chat: Chat) -> Chat:
        self.chats[chat.id] = chat
        return chat

    async def delete(self, chat_id: UUID) -> None:
        self.chats.pop(chat_id, None)

    async def search(self, query: str, limit: int = 10) -> list[Chat]:
        return []

    async def get_user_chats(self, user_id: UUID) -> list[Chat]:
        return []

    async def get_private_chat(self, user_id: UUID, other_user_id: UUID) -> Chat | None:
        if not self._member_repo:
            return None
        for chat in self.chats.values():
            if chat.type != ChatType.PRIVATE:
                continue
            members = await self._member_repo.get_chat_members(chat.id)
            member_ids = {m.user_id for m in members}
            if user_id in member_ids and other_user_id in member_ids:
                return chat
        return None

    async def get_private_chat_including_deleted(self, user_id: UUID, other_user_id: UUID) -> Chat | None:
        if not self._member_repo:
            return None
        for chat in self.chats.values():
            if chat.type != ChatType.PRIVATE:
                continue
            members = await self._member_repo.get_chat_members_including_deleted(chat.id)
            member_ids = {m.user_id for m in members}
            if user_id in member_ids and other_user_id in member_ids:
                return chat
        return None


class FakeChatMemberRepository(AbstractChatMemberRepository):
    def __init__(self):
        self.members: dict[tuple[UUID, UUID], ChatMember] = {}  # (user_id, chat_id) → ChatMember

    async def get_member(self, user_id: UUID, chat_id: UUID) -> ChatMember | None:
        member = self.members.get((user_id, chat_id))
        if member and member.deleted_at is None:
            return member
        return None

    async def get_member_including_deleted(self, user_id: UUID, chat_id: UUID) -> ChatMember | None:
        return self.members.get((user_id, chat_id))

    async def get_chat_members(self, chat_id: UUID, limit: int = 50, offset: int = 0) -> list[ChatMember]:
        return [
            m for m in self.members.values()
            if m.chat_id == chat_id and m.deleted_at is None
        ]

    async def get_chat_members_including_deleted(self, chat_id: UUID) -> list[ChatMember]:
        """Для fake — все участники включая soft-deleted"""
        return [m for m in self.members.values() if m.chat_id == chat_id]

    async def get_user_memberships(self, user_id: UUID) -> list[ChatMember]:
        return [
            m for m in self.members.values()
            if m.user_id == user_id and m.deleted_at is None
        ]

    async def save(self, chat_member: ChatMember) -> ChatMember:
        self.members[(chat_member.user_id, chat_member.chat_id)] = chat_member
        return chat_member

    async def delete(self, user_id: UUID, chat_id: UUID) -> None:
        self.members.pop((user_id, chat_id), None)