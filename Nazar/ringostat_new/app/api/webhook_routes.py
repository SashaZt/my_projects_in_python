# app/api/webhook_routes.py
from typing import Optional

from app.core.dependencies import get_db
from app.schemas.webhook import (
    WebhookProcessingResult,
    WebhookRegister,
    WebhookResponse,
)
from app.services.webhook_service import WebhookService
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
    responses={404: {"description": "Not found"}},
)


@router.post("/register", response_model=WebhookResponse)
async def register_webhook(
    webhook_data: WebhookRegister, db: AsyncSession = Depends(get_db)
):
    """Регистрация webhook URL для организации"""
    try:
        logger.info(
            f"Registering webhook for organization: {webhook_data.organization_id}"
        )
        result = await WebhookService.register_webhook(
            db, webhook_data.organization_id, str(webhook_data.webhook_url)
        )
        return result
    except Exception as e:
        logger.error(f"Error registering webhook: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to register webhook: {str(e)}"
        )


@router.get("/organization/{organization_id}", response_model=WebhookResponse)
async def get_organization_webhook(
    organization_id: int, db: AsyncSession = Depends(get_db)
):
    """Получение информации о webhook для организации"""
    try:
        webhook_info = await WebhookService.get_organization_webhook(
            db, organization_id
        )
        if not webhook_info:
            raise HTTPException(
                status_code=404,
                detail=f"No webhook found for organization ID: {organization_id}",
            )
        return webhook_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting webhook: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get webhook information: {str(e)}"
        )


@router.post("/process/{organization_id}", response_model=WebhookProcessingResult)
async def process_webhooks(
    organization_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Запуск обработки webhook в фоновом режиме для организации"""
    try:
        # Проверяем существование webhook для организации
        webhook_info = await WebhookService.get_organization_webhook(
            db, organization_id
        )
        if not webhook_info:
            raise HTTPException(
                status_code=404,
                detail=f"No webhook found for organization ID: {organization_id}",
            )

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting webhook processing: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start webhook processing: {str(e)}"
        )


@router.post("/process-sync/{organization_id}", response_model=WebhookProcessingResult)
async def process_webhooks_sync(
    organization_id: int,
    limit: int = Query(
        10, description="Максимальное количество обрабатываемых бронирований"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Синхронная обработка webhook для организации"""
    try:
        # Проверяем существование webhook для организации
        webhook_info = await WebhookService.get_organization_webhook(
            db, organization_id
        )
        if not webhook_info:
            raise HTTPException(
                status_code=404,
                detail=f"No webhook found for organization ID: {organization_id}",
            )

        # Обрабатываем webhook синхронно
        result = await WebhookService.process_pending_webhooks(
            db, organization_id, limit
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhooks: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process webhooks: {str(e)}"
        )


@router.get("/pending", response_model=dict)
async def list_pending_webhooks(
    organization_id: Optional[int] = Query(
        None, description="Фильтр по ID организации"
    ),
    limit: int = Query(100, description="Максимальное количество записей"),
    db: AsyncSession = Depends(get_db),
):
    """Получение списка ожидающих отправки webhook"""
    try:
        # Если указан ID организации, получаем ожидающие webhook только для этой организации
        if organization_id:
            pending_webhooks = await WebhookService.get_pending_webhooks(
                db, organization_id, limit
            )
            return {
                "organization_id": organization_id,
                "pending_count": len(pending_webhooks),
                "webhook_status": (
                    "active" if len(pending_webhooks) > 0 else "no_pending"
                ),
            }
        else:
            # Если ID организации не указан, получаем сводную информацию по всем организациям
            from app.models.organization_webhook import OrganizationWebhook
            from sqlalchemy import select

            # Получаем все активные организации с webhook
            query = select(OrganizationWebhook).where(
                OrganizationWebhook.active == True
            )
            result = await db.execute(query)
            organizations = result.scalars().all()

            # Формируем отчет
            report = {"total_organizations": len(organizations), "organizations": []}

            for org in organizations:
                pending_webhooks = await WebhookService.get_pending_webhooks(
                    db, org.organization_id, limit=10
                )
                report["organizations"].append(
                    {
                        "organization_id": org.organization_id,
                        "pending_count": len(pending_webhooks),
                        "webhook_url": org.webhook_url,
                    }
                )

            return report
    except Exception as e:
        logger.error(f"Error listing pending webhooks: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list pending webhooks: {str(e)}"
        )
