from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    code: int = 200
    msg: str = "success"
    data: object | None = None
    request_id: str
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
