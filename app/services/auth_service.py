from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import verify_password
from app.models.user import User


def create_access_token(user: User) -> str:
    settings = get_settings()
    expire_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user.id), "username": user.username, "exp": expire_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_user_id(token: str) -> int:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise UnauthorizedError("invalid token") from exc
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.isdigit():
        raise UnauthorizedError("invalid token subject")
    return int(subject)


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def authenticate(self, username: str, password: str) -> User:
        user = self.db.query(User).filter(User.username == username).one_or_none()
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("invalid username or password")
        if not user.is_active:
            raise UnauthorizedError("user is inactive")
        return user

    def get_user_by_token(self, token: str) -> User:
        user_id = decode_user_id(token)
        user = self.db.query(User).filter(User.id == user_id).one_or_none()
        if user is None or not user.is_active:
            raise UnauthorizedError("user not found")
        return user
