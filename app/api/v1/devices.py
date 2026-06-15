from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.deps import DbSession, require_permission
from app.schemas.device import DeviceCreate, DeviceListOut, DeviceOut, DeviceUpdate
from app.services.device_service import DeviceService
from app.utils.responses import success_response

router = APIRouter(prefix="/devices", tags=["devices"])
DeviceViewer = Annotated[object, Depends(require_permission("device:view"))]
DeviceAdmin = Annotated[object, Depends(require_permission("device:admin"))]


@router.post("")
def create_device(
    payload: DeviceCreate, request: Request, db: DbSession, _: DeviceAdmin
) -> dict[str, object]:
    device = DeviceService(db).create(payload)
    return success_response(request, DeviceOut.model_validate(device).model_dump(mode="json"))


@router.get("")
def list_devices(request: Request, db: DbSession, _: DeviceViewer) -> dict[str, object]:
    devices = DeviceService(db).list()
    items = [DeviceOut.model_validate(device) for device in devices]
    data = DeviceListOut(items=items, total=len(items)).model_dump(mode="json")
    return success_response(request, data)


@router.get("/{device_id}")
def get_device(
    device_id: str, request: Request, db: DbSession, _: DeviceViewer
) -> dict[str, object]:
    device = DeviceService(db).get(device_id)
    return success_response(request, DeviceOut.model_validate(device).model_dump(mode="json"))


@router.put("/{device_id}")
def update_device(
    device_id: str, payload: DeviceUpdate, request: Request, db: DbSession, _: DeviceAdmin
) -> dict[str, object]:
    device = DeviceService(db).update(device_id, payload)
    return success_response(request, DeviceOut.model_validate(device).model_dump(mode="json"))
