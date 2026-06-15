from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.deps import CurrentUser, DbSession, require_permission
from app.schemas.battery import BatteryQueryRequest
from app.services.command_service import CommandService
from app.utils.responses import success_response

router = APIRouter(prefix="/devices/{device_id}/battery", tags=["battery"])
BatteryViewer = Annotated[object, Depends(require_permission("device:battery:query"))]


@router.post("/query")
async def query_battery(
    device_id: str,
    payload: BatteryQueryRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _: BatteryViewer,
) -> dict[str, object]:
    data = await CommandService(db).dispatch(
        device_id, "battery.query", payload.model_dump(), user.id
    )
    return success_response(request, data)
