import logging
import uuid
from collections.abc import AsyncIterator

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from httpx_oauth.oauth2 import OAuth2

from app import models
from app.api.deps import get_user_db
from app.config import settings
from app.models import User

logger = logging.getLogger(__name__)

oauth_client = OAuth2(
    name=settings.oauth_name,
    client_id=settings.oauth_client_id,
    client_secret=settings.oauth_client_secret,
    authorize_endpoint=settings.oauth_authorize_endpoint,
    access_token_endpoint=settings.oauth_access_token_endpoint,
    refresh_token_endpoint=settings.oauth_refresh_token_endpoint,
    revoke_token_endpoint=settings.oauth_revoke_token_endpoint,
)


class UserManager(UUIDIDMixin, BaseUserManager[models.User, uuid.UUID]):
    """FastAPI Users manager."""

    reset_password_token_secret = settings.fastapi_secret_key
    verification_token_secret = settings.fastapi_secret_key

    async def on_after_register(
        self, user: models.User, request: Request | None = None
    ) -> None:
        """
        Run after a User registers.

        :param user:
        :param request:
        :return:
        """
        logger.info(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: models.User, token: str, request: Request | None = None
    ) -> None:
        """
        Run after a User forgets their password.

        :param user:
        :param token:
        :param request:
        :return:
        """
        logger.info(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: models.User, token: str, request: Request | None = None
    ) -> None:
        """
        Run after a User requests to verify.

        :param user:
        :param token:
        :param request:
        :return:
        """
        logger.info(
            f"Verification requested for user {user.id}. Verification token: {token}"
        )


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[User, uuid.UUID] = Depends(get_user_db),
) -> AsyncIterator[UserManager]:
    """
    Retrieve the user manager.

    :param user_db:
    :return:
    """
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy[User, uuid.UUID]:
    """
    JSON web token authentication strategy.

    :return:
    """
    return JWTStrategy(secret=settings.fastapi_secret_key, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[models.User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
