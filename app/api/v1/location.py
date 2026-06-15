from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.deps import CurrentUser, DbSession, require_permission
from app.schemas.location import LocationQueryRequest
from app.services.command_service import CommandService
from app.utils.responses import success_response

router = APIRouter(prefix="/devices/{device_id}/location", tags=["location"])
LocationViewer = Annotated[object, Depends(require_permission("device:location:query"))]


@router.post("/query")
async def query_location(
    device_id: str,
    payload: LocationQueryRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _: LocationViewer,
) -> dict[str, object]:
    data = await CommandService(db).dispatch(
        device_id, "location.query", payload.model_dump(), user.id
    )
    return success_response(request, data)
