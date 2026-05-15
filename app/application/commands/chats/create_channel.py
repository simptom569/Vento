from dataclasses import dataclass
from uuid import UUID, uuid4
from datetime import datetime, UTC

from app.domain.entities.chat import Chat, ChatMember
from app.domain.entities.enums import ChatRole, ChatType
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository
from app.domain.exceptions import AlreadyExistsError


@dataclass
class CreateChannelCommand:
    actor_id: UUID
    title: str
    username: str | None = None
    avatar_url: str | None = None
    is_public: bool = False


class CreateChannelHandler:
    def __init__(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ):
        self.chat_repo = chat_repo
        self.chat_member_repo = chat_member_repo
    
    async def handle(self, cmd: CreateChannelCommand) -> Chat:
        if cmd.username:
            existing = await self.chat_repo.get_by_username(cmd.username)
            if existing:
                raise AlreadyExistsError("Канал с таким @username уже существует")
        
        channel = Chat(
            id=uuid4(),
            type=ChatType.CHANNEL,
            created_by=cmd.actor_id,
            created_at=datetime.now(UTC),
            title=cmd.title,
            username=cmd.username,
            avatar_url=cmd.avatar_url,
            is_public=cmd.is_public,
        )
        
        chat_member = ChatMember(
            id=uuid4(),
            chat_id=channel.id,
            user_id=cmd.actor_id,
            joined_at=datetime.now(UTC),
            role=ChatRole.OWNER,
        )
        
        channel.add_member()
        
        await self.chat_repo.save(channel)
        await self.chat_member_repo.save(chat_member)
        
        return channel