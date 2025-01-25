from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.core.dependencies import get_db
from app.models.telegram_message import TelegramMessage
from app.schemas.telegram import TelegramMessageSchema
from configuration.logger_setup import logger

router = APIRouter()


@router.get("/telegram/messages", response_model=list[TelegramMessageSchema])
async def get_all_telegram_messages(db: AsyncSession = Depends(get_db)):
    """
    Получить все сообщения Telegram с данными отправителя и получателя.

    :param db: Асинхронная сессия базы данных.
    :return: Список сообщений с полными данными.
    """
    try:
        # Используем joinedload для подгрузки связанных данных
        query = select(TelegramMessage).options(
            joinedload(TelegramMessage.sender),  # Загружаем отправителя
            joinedload(TelegramMessage.recipient),  # Загружаем получателя
        )
        result = await db.execute(query)
        messages = result.scalars().all()

        if not messages:
            logger.info("Сообщения отсутствуют в базе данных.")
            return []

        # Сериализация сообщений
        serialized_messages = [
            TelegramMessageSchema(
                sender={
                    "name": message.sender.name,
                    "username": message.sender.username,
                    "telegram_id": message.sender.telegram_id,
                    "phone": message.sender.phone,
                },
                recipient={
                    "name": message.recipient.name,
                    "username": message.recipient.username,
                    "telegram_id": message.recipient.telegram_id,
                    "phone": message.recipient.phone,
                },
                message={"text": message.message},
            )
            for message in messages
        ]

        logger.info(f"Получено {len(serialized_messages)} сообщений из базы данных.")
        return serialized_messages

    except Exception as e:
        logger.error(f"Ошибка при получении сообщений: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка при получении сообщений: {e}"
        )
