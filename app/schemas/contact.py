from app.schemas.command import PagedQueryRequest


class ContactQueryRequest(PagedQueryRequest):
    phone_number: str | None = None
    name: str | None = None
