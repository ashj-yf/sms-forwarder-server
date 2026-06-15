from abc import ABC, abstractmethod
from typing import Any


class DeviceChannelAdapter(ABC):
    @abstractmethod
    async def request(
        self, base_url: str, path: str, payload: dict[str, Any], secret: str | None
    ) -> dict[str, Any]:
        raise NotImplementedError
