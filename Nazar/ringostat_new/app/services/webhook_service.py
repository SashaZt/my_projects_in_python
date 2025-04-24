# app/services/webhook_service.py
import asyncio
import time
from typing import Any, Dict, List, Optional

import aiohttp
from app.models.organization_webhook import OrganizationWebhook
from app.models.reservation import Reservation
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


class WebhookService:
    """Service for handling webhook operations."""

    @staticmethod
    async def register_webhook(
        db: AsyncSession, organization_id: int, webhook_url: str
    ) -> Dict[str, Any]:
        """Register or update a webhook URL for an organization."""
        try:
            # Проверяем, существует ли запись для данной организации
            query = select(OrganizationWebhook).where(
                OrganizationWebhook.organization_id == organization_id
            )
            result = await db.execute(query)
            existing_webhook = result.scalars().first()

            if existing_webhook:
                # Обновляем существующую запись
                await db.execute(
                    update(OrganizationWebhook)
                    .where(OrganizationWebhook.organization_id == organization_id)
                    .values(webhook_url=webhook_url, active=True)
                )
                await db.commit()
                logger.info(f"Updated webhook for organization ID: {organization_id}")
                return {
                    "organization_id": organization_id,
                    "webhook_url": webhook_url,
                    "active": True,
                    "message": "Webhook updated successfully",
                }
            else:
                # Создаем новую запись
                new_webhook = OrganizationWebhook(
                    organization_id=organization_id,
                    webhook_url=webhook_url,
                    active=True,
                )
                db.add(new_webhook)
                await db.commit()
                logger.info(
                    f"Registered new webhook for organization ID: {organization_id}"
                )
                return {
                    "organization_id": organization_id,
                    "webhook_url": webhook_url,
                    "active": True,
                    "message": "Webhook registered successfully",
                }
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Error registering webhook for organization {organization_id}: {str(e)}"
            )
            raise

    @staticmethod
    async def get_organization_webhook(
        db: AsyncSession, organization_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get webhook information for an organization."""
        try:
            query = select(OrganizationWebhook).where(
                OrganizationWebhook.organization_id == organization_id
            )
            result = await db.execute(query)
            webhook = result.scalars().first()

            if not webhook:
                logger.warning(
                    f"No webhook found for organization ID: {organization_id}"
                )
                return None

            return {
                "organization_id": webhook.organization_id,
                "webhook_url": webhook.webhook_url,
                "active": webhook.active,
                "created_at": webhook.created_at,
            }
        except Exception as e:
            logger.error(
                f"Error retrieving webhook for organization {organization_id}: {str(e)}"
            )
            raise

    @staticmethod
    async def get_pending_webhooks(
        db: AsyncSession, organization_id: int, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get reservations that need webhook delivery for a specific organization."""
        try:
            logger.info(
                f"Ищем бронирования для organizationId={organization_id} с status_webhook=False"
            )

            # Проверка, что организация существует
            org_query = select(OrganizationWebhook).where(
                OrganizationWebhook.organization_id == organization_id
            )
            org_result = await db.execute(org_query)
            org = org_result.scalars().first()
            logger.info(f"Найдена организация: {org is not None}")

            # Проверяем все бронирования для организации, независимо от status_webhook
            all_query = select(Reservation).where(
                Reservation.organizationId == organization_id
            )
            all_result = await db.execute(all_query)
            all_reservations = all_result.scalars().all()
            logger.info(f"Всего бронирований для организации: {len(all_reservations)}")

            # Получаем бронирования, для которых еще не отправлены webhook-уведомления
            query = (
                select(Reservation)
                .where(
                    Reservation.organizationId == organization_id,
                    Reservation.status_webhook == False,
                )
                .limit(limit)
            )

            result = await db.execute(query)
            reservations = result.scalars().all()
            logger.info(f"Из них с status_webhook=False: {len(reservations)}")

            # Формируем данные для отправки
            reservation_list = []
            for reservation in reservations:
                # Получаем связанного клиента
                from app.services.reservation_service import ReservationService

                reservation_data = await ReservationService.get_reservation(
                    db, reservation.id
                )
                if reservation_data:
                    reservation_list.append(reservation_data)
            logger.info(
                f"Found {len(reservation_list)} pending webhooks for organization ID: {organization_id}"
            )
            return reservation_list
        except Exception as e:
            logger.error(
                f"Error retrieving pending webhooks for organization {organization_id}: {str(e)}"
            )
            raise

    @staticmethod
    async def send_webhook(
        db: AsyncSession,
        organization_id: int,
        reservation_id: str,
        webhook_url: str,
        payload: Dict[str, Any],
    ) -> bool:
        """Send webhook for a reservation."""
        try:
            # Преобразуем данные в нужный формат (если payload получен через get_reservation)
            # Текущий payload может содержать данные в виде ReservationResponse
            # Преобразуем их в формат, показанный в примере
            formatted_payload = [
                {
                    "id": payload["id"],
                    "organizationId": payload["organizationId"],
                    "customer": payload["customer"],
                    "rooms": payload["rooms"],
                    "status": payload["status"],
                    "services": payload["services"],
                    "bookedAt": payload["bookedAt"],
                    "modifiedAt": payload["modifiedAt"],
                    "source": payload["source"],
                    "responsibleUserId": payload["responsibleUserId"],
                }
            ]
            # Отправляем webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url, json=formatted_payload
                ) as response:
                    success = response.status in (200, 201)

                    if success:
                        # Обновляем статус отправки webhook
                        await db.execute(
                            update(Reservation)
                            .where(Reservation.id == reservation_id)
                            .values(status_webhook=True)
                        )
                        await db.commit()
                        logger.info(
                            f"Successfully sent webhook for reservation ID: {reservation_id}"
                        )
                    else:
                        logger.warning(
                            f"Failed to send webhook for reservation ID: {reservation_id}. "
                            f"Status code: {response.status}"
                        )

                    return success
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Error sending webhook for reservation {reservation_id}: {str(e)}"
            )
            return False

    @staticmethod
    async def process_pending_webhooks(
        db: AsyncSession, organization_id: int, limit: int = 10
    ) -> Dict[str, Any]:
        """Process all pending webhooks for an organization."""
        try:
            # Получаем информацию о webhook URL для организации
            webhook_info = await WebhookService.get_organization_webhook(
                db, organization_id
            )

            if not webhook_info or not webhook_info.get("active"):
                logger.warning(
                    f"No active webhook found for organization ID: {organization_id}"
                )
                return {
                    "success": False,
                    "message": "No active webhook configuration found",
                    "processed": 0,
                    "failed": 0,
                }

            # Получаем все ожидающие отправки бронирования
            pending_reservations = await WebhookService.get_pending_webhooks(
                db, organization_id, limit
            )

            if not pending_reservations:
                logger.info(
                    f"No pending webhooks found for organization ID: {organization_id}"
                )
                return {
                    "success": True,
                    "message": "No pending webhooks found",
                    "processed": 0,
                    "failed": 0,
                }

            # Отправляем webhook для каждого бронирования
            processed = 0
            failed = 0

            for reservation in pending_reservations:
                success = await WebhookService.send_webhook(
                    db,
                    organization_id,
                    reservation["id"],
                    webhook_info["webhook_url"],
                    reservation,
                )

                if success:
                    processed += 1
                else:
                    failed += 1
            await asyncio.sleep(3)
            return {
                "success": failed == 0,
                "message": f"Processed {processed} webhooks, failed {failed}",
                "processed": processed,
                "failed": failed,
            }
        except Exception as e:
            logger.error(
                f"Error processing webhooks for organization {organization_id}: {str(e)}"
            )
            raise
