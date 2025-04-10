# app/schemas/webhook.py
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, HttpUrl


class WebhookRegister(BaseModel):
    """Schema for registering a webhook."""

    organization_id: int
    webhook_url: HttpUrl


class WebhookResponse(BaseModel):
    """Schema for webhook response."""

    organization_id: int
    webhook_url: str
    active: bool
    message: Optional[str] = None
    created_at: Optional[int] = None


class WebhookProcessingResult(BaseModel):
    """Schema for webhook processing results."""

    success: bool
    message: str
    processed: int
    failed: int
    details: Optional[List[Dict[str, Any]]] = None
