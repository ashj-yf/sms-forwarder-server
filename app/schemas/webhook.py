from pydantic import BaseModel


class WebhookOut(BaseModel):
    webhook_url: str
    webhook_token: str


class WebhookIngestOut(BaseModel):
    duplicate: bool
    event_id: str
    event_type: str
