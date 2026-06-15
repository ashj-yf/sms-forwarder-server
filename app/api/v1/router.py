from fastapi import APIRouter, Request

from app.api.v1 import (
    auth,
    battery,
    calls,
    config,
    contacts,
    devices,
    frps,
    location,
    sms,
    tunnels,
    webhooks,
)
from app.utils.responses import success_response

router = APIRouter()
router.include_router(auth.router)
router.include_router(devices.router)
router.include_router(webhooks.router)
router.include_router(tunnels.router)
router.include_router(frps.router)
router.include_router(config.router)
router.include_router(sms.router)
router.include_router(calls.router)
router.include_router(contacts.router)
router.include_router(battery.router)
router.include_router(location.router)


@router.get("/healthz")
def healthz(request: Request) -> dict[str, object]:
    return success_response(request, {"status": "ok"})
