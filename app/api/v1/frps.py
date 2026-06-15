from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import DbSession, require_permission
from app.services.frps_service import FrpsService
from app.utils.responses import success_response

router = APIRouter(prefix="/frps", tags=["frps"])
FrpsViewer = Annotated[object, Depends(require_permission("device:view"))]


@router.get("/devices")
def list_frps_devices(
    request: Request,
    db: DbSession,
    _: FrpsViewer,
    connected_only: bool = Query(default=False),
) -> dict[str, object]:
    data = FrpsService(db).list_devices(connected_only=connected_only)
    return success_response(request, data.model_dump(mode="json"))
