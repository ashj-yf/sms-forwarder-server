from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from app.api.deps import DbSession, require_permission
from app.core.config import get_settings
from app.services.webhook_service import WebhookService
from app.utils.rate_limiter import check_rate_limit
from app.utils.responses import success_response

router = APIRouter(tags=["webhooks"])
WebhookManager = Annotated[object, Depends(require_permission("device:webhook:manage"))]


@router.post("/devices/{device_id}/webhook")
def create_webhook(
    device_id: str, request: Request, db: DbSession, _: WebhookManager
) -> dict[str, object]:
    data = WebhookService(db).create(device_id)
    return success_response(request, data)


@router.post("/devices/{device_id}/webhook/rotate")
def rotate_webhook(
    device_id: str, request: Request, db: DbSession, _: WebhookManager
) -> dict[str, object]:
    data = WebhookService(db).rotate(device_id)
    return success_response(request, data)


@router.post("/webhooks/smsforwarder/{webhook_token}")
async def ingest_webhook(webhook_token: str, request: Request, db: DbSession) -> dict[str, object]:
    settings = get_settings()
    check_rate_limit(db, f"webhook:{webhook_token[:8]}", settings.webhook_rate_limit_per_minute)
    payload: dict[str, Any] = await request.json()
    service = WebhookService(db)
    webhook = service.lookup(webhook_token)
    source_ip = request.client.host if request.client else None
    data = service.ingest(webhook, payload, source_ip)
    msg = "duplicate ignored" if data["duplicate"] else "success"
    return success_response(request, data, msg)
