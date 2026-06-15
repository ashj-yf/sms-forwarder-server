from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.utils.masking import scrub


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        action: str,
        result: str,
        detail: dict[str, Any] | None = None,
        user_id: int | None = None,
        device_id: str | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        log = AuditLog(
            user_id=user_id,
            action=action,
            device_id=device_id,
            client_ip=client_ip,
            user_agent=user_agent,
            result=result,
            detail=scrub(detail or {}),
        )
        self.db.add(log)
