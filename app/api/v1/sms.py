from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.deps import CurrentUser, DbSession, require_permission
from app.schemas.sms import SmsQueryRequest
from app.services.command_service import CommandService
from app.utils.responses import success_response

router = APIRouter(prefix="/devices/{device_id}/sms", tags=["sms"])
SmsViewer = Annotated[object, Depends(require_permission("device:sms:query"))]


@router.post("/query")
async def query_sms(
    device_id: str,
    payload: SmsQueryRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _: SmsViewer,
) -> dict[str, object]:
    data = await CommandService(db).dispatch(device_id, "sms.query", payload.model_dump(), user.id)
    return success_response(request, data)
