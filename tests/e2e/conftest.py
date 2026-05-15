from typing import AsyncIterator

import pytest
from httpx import AsyncClient, ASGITransport
from dishka import make_async_container, Provider, Scope, provide
from dishka.integrations.fastapi import setup_dishka
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.domain.ports.repositories.user_repo import AbstractUserRepository
from app.domain.ports.repositories.credentials_repo import AbstractCredentialsRepository
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository
from app.infrastructure.db.repositories.user_repo import UserRepository
from app.infrastructure.db.repositories.credentials_repo import CredentialsRepository
from app.infrastructure.db.repositories.chat_repo import ChatRepository
from app.infrastructure.db.repositories.chat_member_repo import ChatMemberRepository
from app.application.commands.auth.register import RegisterHandler
from app.application.commands.auth.login import LoginHandler
from app.application.commands.auth.refresh_token import RefreshTokenHandler
from app.application.commands.auth.logout import LogoutHandler
from app.application.commands.chats.create_group import CreateGroupHandler
from app.application.commands.chats.create_channel import CreateChannelHandler
from app.application.commands.chats.open_private_chat import OpenPrivateChatHandler
from app.application.commands.chats.delete_chat import DeleteChatHandler
from app.application.commands.chats.update_group import UpdateGroupHandler
from app.application.commands.chats.update_channel import UpdateChannelHandler
from app.application.commands.chats.mute_chat import MuteChatHandler
from app.application.commands.chats.join_chat import JoinChatHandler
from app.application.commands.chats.leave_chat import LeaveChatHandler
from app.application.commands.chats.add_member import AddMemberHandler
from app.application.commands.chats.remove_member import RemoveMemberHandler
from app.application.commands.chats.change_member_role import ChangeMemberRoleHandler
from app.application.queries.chats.get_user_chats import GetUserChatsHandler
from app.application.queries.chats.get_chat import GetChatHandler
from app.application.queries.chats.get_chat_members import GetChatMembersHandler


class TestProvider(Provider):
    """Тестовый контейнер — использует тестовую БД"""

    def __init__(self, session_factory):
        super().__init__()
        self._session_factory = session_factory

    @provide(scope=Scope.REQUEST)
    async def get_session(self) -> AsyncIterator[AsyncSession]:
        async with self._session_factory() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def get_user_repo(self, session: AsyncSession) -> AbstractUserRepository:
        return UserRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_credentials_repo(self, session: AsyncSession) -> AbstractCredentialsRepository:
        return CredentialsRepository(session)
    
    @provide(scope=Scope.REQUEST)
    def get_chat_repo(self, session: AsyncSession) -> AbstractChatRepository:
        return ChatRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_chat_member_repo(self, session: AsyncSession) -> AbstractChatMemberRepository:
        return ChatMemberRepository(session)
    
    @provide(scope=Scope.REQUEST)
    def get_register_handler(
        self,
        user_repo: AbstractUserRepository,
        credentials_repo: AbstractCredentialsRepository,
    ) -> RegisterHandler:
        return RegisterHandler(user_repo=user_repo, credentials_repo=credentials_repo)
    
    @provide(scope=Scope.REQUEST)
    def get_login_handler(
        self,
        user_repo: AbstractUserRepository,
        credentials_repo: AbstractCredentialsRepository,
    ) -> LoginHandler:
        return LoginHandler(user_repo=user_repo, credentials_repo=credentials_repo)
    
    @provide(scope=Scope.REQUEST)
    def get_refresh_token_handler(
        self,
        credentials_repo: AbstractCredentialsRepository,
    ) -> RefreshTokenHandler:
        return RefreshTokenHandler(credentials_repo=credentials_repo)
    
    @provide(scope=Scope.REQUEST)
    def get_logout_handler(
        self,
        credentials_repo: AbstractCredentialsRepository,
    ) -> LogoutHandler:
        return LogoutHandler(credentials_repo=credentials_repo)
    
    @provide(scope=Scope.REQUEST)
    def get_create_group_handler(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ) -> CreateGroupHandler:
        return CreateGroupHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    @provide(scope=Scope.REQUEST)
    def get_create_channel_handler(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ) -> CreateChannelHandler:
        return CreateChannelHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    @provide(scope=Scope.REQUEST)
    def get_open_private_chat_handler(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
        user_repo: AbstractUserRepository,
    ) -> OpenPrivateChatHandler:
        return OpenPrivateChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo, user_repo=user_repo)

    @provide(scope=Scope.REQUEST)
    def get_delete_chat_handler(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ) -> DeleteChatHandler:
        return DeleteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    @provide(scope=Scope.REQUEST)
    def get_update_group_handler(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ) -> UpdateGroupHandler:
        return UpdateGroupHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    @provide(scope=Scope.REQUEST)
    def get_update_channel_handler(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ) -> UpdateChannelHandler:
        return UpdateChannelHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    @provide(scope=Scope.REQUEST)
    def get_mute_chat_handler(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ) -> MuteChatHandler:
        return MuteChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    @provide(scope=Scope.REQUEST)
    def get_join_chat_handler(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ) -> JoinChatHandler:
        return JoinChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    @provide(scope=Scope.REQUEST)
    def get_leave_chat_handler(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ) -> LeaveChatHandler:
        return LeaveChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    @provide(scope=Scope.REQUEST)
    def get_add_member_handler(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
        user_repo: AbstractUserRepository,
    ) -> AddMemberHandler:
        return AddMemberHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo, user_repo=user_repo)

    @provide(scope=Scope.REQUEST)
    def get_remove_member_handler(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ) -> RemoveMemberHandler:
        return RemoveMemberHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    @provide(scope=Scope.REQUEST)
    def get_change_member_role_handler(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ) -> ChangeMemberRoleHandler:
        return ChangeMemberRoleHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    @provide(scope=Scope.REQUEST)
    def get_get_chat_handler(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ) -> GetChatHandler:
        return GetChatHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    @provide(scope=Scope.REQUEST)
    def get_get_chat_members_handler(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ) -> GetChatMembersHandler:
        return GetChatMembersHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)

    @provide(scope=Scope.REQUEST)
    def get_get_user_chats_handler(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ) -> GetUserChatsHandler:
        return GetUserChatsHandler(chat_repo=chat_repo, chat_member_repo=chat_member_repo)


@pytest.fixture
async def container(test_session_factory):
    c = make_async_container(TestProvider(test_session_factory))
    yield c
    await c.close()


@pytest.fixture
async def client(container):
    app = create_app()
    setup_dishka(container, app=app)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac