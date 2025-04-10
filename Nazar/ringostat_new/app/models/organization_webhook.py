# app/models/organization_webhook.py
import time

from app.core.base import Base
from sqlalchemy import BigInteger, Boolean, Column, Integer, String


class OrganizationWebhook(Base):
    """Model for storing organization webhook URLs."""

    __tablename__ = "organization_webhooks"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, unique=True, nullable=False)
    webhook_url = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(BigInteger, nullable=False)

    def __init__(self, **kwargs):
        """Initialize with current timestamp if not provided."""
        current_time = int(time.time() * 1000)
        if "created_at" not in kwargs:
            kwargs["created_at"] = current_time
        super().__init__(**kwargs)
