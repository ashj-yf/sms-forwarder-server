from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.deps import CurrentUser, DbSession, require_permission
from app.schemas.tunnel import TunnelEnableIn, TunnelOut, TunnelUpdateIn
from app.services.tunnel_service import TunnelService
from app.utils.responses import success_response

router = APIRouter(prefix="/devices/{device_id}/tunnel", tags=["tunnels"])
TunnelViewer = Annotated[object, Depends(require_permission("device:view"))]
TunnelManager = Annotated[object, Depends(require_permission("device:tunnel:manage"))]


@router.get("")
def get_tunnel(
    device_id: str, request: Request, db: DbSession, _: TunnelViewer
) -> dict[str, object]:
    tunnel = TunnelService(db).get(device_id)
    data = None if tunnel is None else TunnelOut.model_validate(tunnel).model_dump(mode="json")
    return success_response(request, data)


@router.post("")
def enable_tunnel(
    device_id: str, payload: TunnelEnableIn, request: Request, db: DbSession, _: TunnelManager
) -> dict[str, object]:
    tunnel = TunnelService(db).enable(device_id, payload)
    return success_response(request, TunnelOut.model_validate(tunnel).model_dump(mode="json"))


@router.put("")
def update_tunnel(
    device_id: str, payload: TunnelUpdateIn, request: Request, db: DbSession, _: TunnelManager
) -> dict[str, object]:
    tunnel = TunnelService(db).update(device_id, payload)
    return success_response(request, TunnelOut.model_validate(tunnel).model_dump(mode="json"))


@router.delete("")
def disable_tunnel(
    device_id: str, request: Request, db: DbSession, _: TunnelManager
) -> dict[str, object]:
    tunnel = TunnelService(db).disable(device_id)
    return success_response(request, TunnelOut.model_validate(tunnel).model_dump(mode="json"))


@router.post("/rotate-token")
def rotate_tunnel_token(
    device_id: str, request: Request, db: DbSession, _: TunnelManager
) -> dict[str, object]:
    data = TunnelService(db).rotate_token(device_id)
    return success_response(request, data)


@router.get("/frpc-config")
def get_frpc_config(
    device_id: str,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _: TunnelManager,
) -> dict[str, object]:
    data = TunnelService(db).render_frpc_config(device_id, user.id)
    return success_response(request, data.model_dump(mode="json"))
