from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.deps import CurrentUser, DbSession, require_permission
from app.schemas.contact import ContactQueryRequest
from app.services.command_service import CommandService
from app.utils.responses import success_response

router = APIRouter(prefix="/devices/{device_id}/contacts", tags=["contacts"])
ContactViewer = Annotated[object, Depends(require_permission("device:contact:query"))]


@router.post("/query")
async def query_contacts(
    device_id: str,
    payload: ContactQueryRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _: ContactViewer,
) -> dict[str, object]:
    data = await CommandService(db).dispatch(
        device_id, "contact.query", payload.model_dump(), user.id
    )
    return success_response(request, data)
