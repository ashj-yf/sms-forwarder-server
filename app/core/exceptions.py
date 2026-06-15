from enum import IntEnum
from typing import Any


class ErrorCode(IntEnum):
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    RATE_LIMITED = 429
    DEVICE_UNREACHABLE = 502
    DEVICE_TIMEOUT = 504
    INTERNAL_ERROR = 500


class AppError(Exception):
    def __init__(
        self, code: ErrorCode, message: str, details: dict[str, Any] | None = None
    ) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "unauthorized") -> None:
        super().__init__(ErrorCode.UNAUTHORIZED, message)


class ForbiddenError(AppError):
    def __init__(self, message: str = "forbidden") -> None:
        super().__init__(ErrorCode.FORBIDDEN, message)


class NotFoundError(AppError):
    def __init__(self, message: str = "not found") -> None:
        super().__init__(ErrorCode.NOT_FOUND, message)


class ConflictError(AppError):
    def __init__(self, message: str = "conflict") -> None:
        super().__init__(ErrorCode.CONFLICT, message)


class RateLimitError(AppError):
    def __init__(self, message: str = "rate limited", retry_after: int = 60) -> None:
        super().__init__(ErrorCode.RATE_LIMITED, message, {"retry_after": retry_after})


class DeviceChannelError(AppError):
    def __init__(self, message: str = "device channel error") -> None:
        super().__init__(ErrorCode.DEVICE_UNREACHABLE, message)


class DeviceTimeoutError(AppError):
    def __init__(self, message: str = "device timeout") -> None:
        super().__init__(ErrorCode.DEVICE_TIMEOUT, message)
