from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.models.telegram_message import TelegramMessage
from app.schemas.telegram_message import TelegramMessageResponse
from configuration.logger_setup import logger
from sqlalchemy.future import select

router = APIRouter()


@router.get("/telegram/message", response_model=list[TelegramMessageResponse])
async def get_telegram_messages(db: AsyncSession = Depends(get_db)):
    """
    Получает все сообщения Telegram из базы данных.

    :param db: Асинхронная сессия базы данных.
    :return: Список сообщений в формате JSON.
    """
    try:
        # Выполняем запрос для получения всех сообщений
        query = select(TelegramMessage)
        result = await db.execute(query)
        messages = result.scalars().all()

        if not messages:
            logger.info("Сообщения отсутствуют в базе данных.")
            return []

        logger.info(f"Получено {len(messages)} сообщений из базы данных.")
        return messages

    except Exception as e:
        logger.error(f"Ошибка при получении сообщений: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка при получении сообщений: {e}"
        )
