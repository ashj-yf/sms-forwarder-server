from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.deps import CurrentUser, DbSession, require_permission
from app.schemas.config import ConfigQueryRequest
from app.services.command_service import CommandService
from app.utils.responses import success_response

router = APIRouter(prefix="/devices/{device_id}/config", tags=["config"])
ConfigViewer = Annotated[object, Depends(require_permission("device:view"))]


@router.post("/query")
async def query_config(
    device_id: str,
    payload: ConfigQueryRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _: ConfigViewer,
) -> dict[str, object]:
    data = await CommandService(db).dispatch(
        device_id, "config.query", payload.model_dump(), user.id
    )
    return success_response(request, data)
