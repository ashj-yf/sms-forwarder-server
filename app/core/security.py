import bcrypt


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("password is required")
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False
    return bcrypt.checkpw(password.encode(), password_hash.encode())
