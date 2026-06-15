from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.deps import CurrentUser, DbSession, require_permission
from app.schemas.call import CallQueryRequest
from app.services.command_service import CommandService
from app.utils.responses import success_response

router = APIRouter(prefix="/devices/{device_id}/calls", tags=["calls"])
CallViewer = Annotated[object, Depends(require_permission("device:call:query"))]


@router.post("/query")
async def query_calls(
    device_id: str,
    payload: CallQueryRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _: CallViewer,
) -> dict[str, object]:
    data = await CommandService(db).dispatch(device_id, "call.query", payload.model_dump(), user.id)
    return success_response(request, data)
