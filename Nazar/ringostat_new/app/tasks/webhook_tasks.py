# app/tasks/webhook_tasks.py
import asyncio
import time

from app.core.db import get_db_session
from app.models.organization_webhook import OrganizationWebhook
from app.services.webhook_service import WebhookService
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def process_all_webhooks():
    """Periodic task to process webhooks for all organizations."""
    try:
        logger.info("Starting periodic webhook processing")
        async with get_db_session() as db:
            # Получаем все активные организации с webhook
            query = select(OrganizationWebhook).where(
                OrganizationWebhook.active == True
            )
            result = await db.execute(query)
            organizations = result.scalars().all()

            logger.info(
                f"Found {len(organizations)} organizations with active webhooks"
            )

            # Обрабатываем webhook для каждой организации
            for org in organizations:
                try:
                    logger.info(
                        f"Processing webhooks for organization ID: {org.organization_id}"
                    )
                    result = await WebhookService.process_pending_webhooks(
                        db, org.organization_id
                    )
                    logger.info(
                        f"Organization {org.organization_id}: Processed {result['processed']}, "
                        f"Failed {result['failed']}"
                    )
                except Exception as org_error:
                    logger.error(
                        f"Error processing webhooks for organization {org.organization_id}: {str(org_error)}"
                    )
                    # Продолжаем обработку следующей организации

                # Небольшая задержка между организациями
                await asyncio.sleep(0.5)

            logger.info("Completed webhook processing for all organizations")
    except Exception as e:
        logger.error(f"Error in webhook processing task: {str(e)}")


# Функция для запуска в фоновом процессе приложения
async def start_webhook_task(interval_seconds=60):
    """Start periodic webhook processing task."""
    while True:
        try:
            await process_all_webhooks()
        except Exception as e:
            logger.error(f"Error in webhook task: {str(e)}")
        finally:
            # Ждем указанный интервал перед следующей обработкой
            await asyncio.sleep(interval_seconds)
