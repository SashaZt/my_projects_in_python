# app/api/webhooks.py
from app.api.deps import get_db
from app.schemas.webhook import (
    WebhookProcessingResult,
    WebhookRegister,
    WebhookResponse,
)
from app.services.webhook_service import WebhookService
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/register", response_model=WebhookResponse)
async def register_webhook(
    webhook_data: WebhookRegister, db: AsyncSession = Depends(get_db)
):
    """Register a webhook for an organization."""
    try:
        result = await WebhookService.register_webhook(
            db, webhook_data.organization_id, str(webhook_data.webhook_url)
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to register webhook: {str(e)}"
        )


@router.get("/organization/{organization_id}", response_model=WebhookResponse)
async def get_organization_webhook(
    organization_id: int, db: AsyncSession = Depends(get_db)
):
    """Get webhook information for an organization."""
    webhook_info = await WebhookService.get_organization_webhook(db, organization_id)
    if not webhook_info:
        raise HTTPException(
            status_code=404,
            detail=f"No webhook found for organization ID: {organization_id}",
        )
    return webhook_info


@router.post("/process/{organization_id}", response_model=WebhookProcessingResult)
async def process_webhooks(
    organization_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Process pending webhooks for an organization."""
    try:
        # Запускаем обработку в фоновом режиме
        background_tasks.add_task(
            WebhookService.process_pending_webhooks, db, organization_id
        )

        return {
            "success": True,
            "message": f"Webhook processing started for organization ID: {organization_id}",
            "processed": 0,
            "failed": 0,
            "details": None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start webhook processing: {str(e)}"
        )


@router.post("/process-sync/{organization_id}", response_model=WebhookProcessingResult)
async def process_webhooks_sync(
    organization_id: int, db: AsyncSession = Depends(get_db)
):
    """Process pending webhooks for an organization synchronously."""
    try:
        result = await WebhookService.process_pending_webhooks(db, organization_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process webhooks: {str(e)}"
        )
