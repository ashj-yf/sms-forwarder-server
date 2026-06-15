from typing import Literal

from pydantic import BaseModel, Field


class QueryModeRequest(BaseModel):
    mode: Literal["realtime", "cache"] = "realtime"


class PagedQueryRequest(QueryModeRequest):
    page_num: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
