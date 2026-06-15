from app.schemas.command import PagedQueryRequest


class SmsQueryRequest(PagedQueryRequest):
    type: int | None = None
    keyword: str | None = None
