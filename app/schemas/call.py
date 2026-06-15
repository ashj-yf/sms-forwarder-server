from app.schemas.command import PagedQueryRequest


class CallQueryRequest(PagedQueryRequest):
    type: int | None = None
    phone_number: str | None = None
