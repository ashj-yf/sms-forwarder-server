from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.adapters.smsforwarder_http_adapter import SmsForwarderHttpAdapter
from app.core.exceptions import AppError, ConflictError, DeviceChannelError, NotFoundError
from app.models.device import Device
from app.models.device_command_log import DeviceCommandLog
from app.models.device_event import DeviceEvent
from app.utils.crypto import decrypt
from app.utils.id_generator import generate_request_id
from app.utils.masking import scrub

COMMAND_PATHS = {
    "config.query": "/config/query",
    "sms.query": "/sms/query",
    "call.query": "/call/query",
    "contact.query": "/contact/query",
    "battery.query": "/battery/query",
    "location.query": "/location/query",
}
EVENT_TYPES = {
    "sms.query": "sms",
    "call.query": "call",
    "contact.query": "contact",
    "battery.query": "battery",
    "location.query": "location",
}


class CommandService:
    def __init__(self, db: Session, adapter: SmsForwarderHttpAdapter | None = None) -> None:
        self.db = db
        self.adapter = adapter or SmsForwarderHttpAdapter()

    async def dispatch(
        self,
        device_id: str,
        command_type: str,
        payload: dict[str, Any],
        user_id: int | None = None,
    ) -> dict[str, Any]:
        device = self._get_device(device_id)
        mode = str(payload.get("mode", "realtime"))
        command_log = self._create_log(device, command_type, payload, user_id)
        try:
            if mode == "cache":
                data = self._query_cache(device_id, command_type, payload)
            elif mode == "realtime":
                data = await self._query_realtime(device, command_type, payload)
            else:
                raise ConflictError("unsupported query mode")
        except AppError as exc:
            self._finish_log(command_log, "failed", {}, exc.message)
            raise
        except Exception as exc:
            self._finish_log(command_log, "failed", {}, str(exc))
            raise DeviceChannelError("command dispatch failed") from exc
        self._finish_log(command_log, "success", data, None)
        return {"request_id": command_log.request_id, "mode": mode, "result": data}

    def _get_device(self, device_id: str) -> Device:
        device = self.db.query(Device).filter(Device.device_id == device_id).one_or_none()
        if device is None:
            raise NotFoundError("device not found")
        return device

    def _create_log(
        self, device: Device, command_type: str, payload: dict[str, Any], user_id: int | None
    ) -> DeviceCommandLog:
        log = DeviceCommandLog(
            request_id=generate_request_id(),
            device_id=device.device_id,
            user_id=user_id,
            command_type=command_type,
            channel_type=device.channel_type,
            status="pending",
            request_summary=scrub(payload),
            response_summary={},
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    async def _query_realtime(
        self, device: Device, command_type: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        if device.channel_type == "webhook_only":
            raise ConflictError("device only supports cache mode")
        if not device.base_url:
            raise ConflictError("device base_url is required for realtime mode")
        path = COMMAND_PATHS.get(command_type)
        if path is None:
            raise ConflictError("unsupported command type")
        request_payload = {key: value for key, value in payload.items() if key != "mode"}
        secret = decrypt(device.sign_secret_encrypted) if device.sign_secret_encrypted else None
        return await self.adapter.request(device.base_url, path, request_payload, secret)

    def _query_cache(
        self, device_id: str, command_type: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        event_type = EVENT_TYPES.get(command_type)
        if event_type is None:
            raise ConflictError("cache mode is not supported for this command")
        page_num = int(payload.get("page_num", 1))
        page_size = int(payload.get("page_size", 10))
        query = self.db.query(DeviceEvent).filter(
            DeviceEvent.device_id == device_id,
            DeviceEvent.event_type == event_type,
        )
        total = query.count()
        items = (
            query.order_by(DeviceEvent.created_at.desc())
            .offset((page_num - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "items": [item.normalized_payload for item in items],
            "total": total,
            "page_num": page_num,
            "page_size": page_size,
        }

    def _finish_log(
        self,
        command_log: DeviceCommandLog,
        status: str,
        response: dict[str, Any],
        error_msg: str | None,
    ) -> None:
        command_log.status = status
        command_log.response_summary = scrub(response)
        command_log.error_msg = error_msg
        command_log.completed_at = datetime.now(UTC)
        self.db.commit()
