import argparse

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User
from app.models.user_permission import UserPermission

DEFAULT_PERMISSIONS = [
    "admin:*",
    "device:view",
    "device:admin",
    "device:webhook:manage",
    "device:sms:query",
    "device:call:query",
    "device:contact:query",
    "device:battery:query",
    "device:location:query",
]


def create_admin(db: Session, username: str, password: str) -> User:
    user = db.query(User).filter(User.username == username).one_or_none()
    if user is None:
        user = User(username=username, password_hash=hash_password(password), is_active=True)
        db.add(user)
        db.flush()
    else:
        user.password_hash = hash_password(password)
        user.is_active = True
    for permission in DEFAULT_PERMISSIONS:
        exists = (
            db.query(UserPermission)
            .filter(UserPermission.user_id == user.id, UserPermission.permission == permission)
            .one_or_none()
        )
        if exists is None:
            db.add(UserPermission(user_id=user.id, permission=permission, granted=True))
    db.commit()
    db.refresh(user)
    return user


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or reset an admin user")
    parser.add_argument("username")
    parser.add_argument("password")
    args = parser.parse_args()
    with SessionLocal() as db:
        user = create_admin(db, args.username, args.password)
    print(f"admin user ready: {user.username}")


if __name__ == "__main__":
    main()
