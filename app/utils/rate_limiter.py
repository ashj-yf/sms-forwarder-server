from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import RateLimitError
from app.models.rate_limit import RateLimit


def check_rate_limit(db: Session, resource_key: str, limit: int, window_seconds: int = 60) -> None:
    now = datetime.now(UTC)
    window_start = now.replace(second=0, microsecond=0)
    record = (
        db.query(RateLimit)
        .filter(RateLimit.resource_key == resource_key, RateLimit.window_start == window_start)
        .one_or_none()
    )
    if record is None:
        record = RateLimit(resource_key=resource_key, window_start=window_start, request_count=1)
        db.add(record)
        db.commit()
        return
    if record.request_count >= limit:
        retry_after = int((window_start + timedelta(seconds=window_seconds) - now).total_seconds())
        raise RateLimitError(retry_after=max(retry_after, 1))
    record.request_count += 1
    db.commit()
