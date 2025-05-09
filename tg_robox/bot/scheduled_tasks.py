# scheduled_tasks.py
import asyncio
import logging
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from db.models import Review
from db.database import get_session_maker
from config.config import Config
from config.logger import logger


async def publish_approved_reviews(bot):
    """Публикация одобренных отзывов в группе"""
    try:
        async with get_session_maker() as session:
            # Получаем отзывы, которые одобрены, но ещё не опубликованы
            stmt = (
                select(Review)
                .options(joinedload(Review.user), joinedload(Review.order))
                .where(Review.is_approved == True, Review.is_published == False)
                .order_by(Review.created_at.asc())
            )
            result = await session.execute(stmt)
            reviews = result.scalars().all()

            if not reviews:
                logger.info("Нет новых одобренных отзывов для публикации")
                return

            group_id = "-4763327238"  # ID группы с отзывами

            for review in reviews:
                user = review.user
                user_name = user.first_name or "Користувач"

                # Формируем текст отзыва
                review_text = (
                    f"📝 <b>Відгук від клієнта</b>\n\n"
                    f"👤 {user_name}\n"
                    f"{'⭐️' * rating}\n\n"
                    f"💬 {review.comment}\n\n"
                    f"📅 {review.created_at.strftime('%d.%m.%Y')}"
                )

                # Публикуем отзыв в группе
                await bot.send_message(chat_id=group_id, text=review_text)

                # Отмечаем отзыв как опубликованный
                review.is_published = True

            # Сохраняем изменения
            await session.commit()

    except Exception as e:
        logger.error(f"Ошибка при публикации одобренных отзывов: {e}")
