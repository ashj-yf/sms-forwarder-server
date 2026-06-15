from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.session import get_session
from app.models.user import User
from app.models.user_permission import UserPermission
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    yield from get_session()


DbSession = Annotated[Session, Depends(get_db)]
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def get_current_user(db: DbSession, credentials: BearerCredentials) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("missing bearer token")
    return AuthService(db).get_user_by_token(credentials.credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permission(permission: str):
    def checker(db: DbSession, user: CurrentUser) -> User:
        if not user.is_active:
            raise ForbiddenError("user is inactive")
        if _has_permission(db, user.id, permission):
            return user
        raise ForbiddenError("permission denied")

    return checker


def _has_permission(db: Session, user_id: int, permission: str) -> bool:
    if permission == "":
        return True
    record = (
        db.query(UserPermission)
        .filter(
            UserPermission.user_id == user_id,
            UserPermission.granted.is_(True),
            or_(UserPermission.permission == permission, UserPermission.permission == "admin:*"),
        )
        .first()
    )
    return record is not None
