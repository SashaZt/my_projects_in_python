# client_import_live.py
import asyncio
import json
import sys
from datetime import date, datetime
from pathlib import Path

import httpx
from config.config import API_BASE_URL
from config.logger import logger


async def import_live_streams(live_data):
    """Импорт данных трансляций через API"""
    try:
        async with httpx.AsyncClient(verify=False) as client:
            # Перебираем каждый элемент в списке live_data
            for user_data in live_data:
                # В каждом элементе может быть только один ключ (TikTok ID)
                for tiktok_id, streams in user_data.items():
                    logger.info(
                        f"Импорт {len(streams)} трансляций для пользователя с TikTok ID: {tiktok_id}"
                    )

                    # Используем эндпоинт массового импорта
                    try:
                        response = await client.post(
                            f"{API_BASE_URL}/live/import-bulk",
                            params={"tiktok_id": tiktok_id},
                            json=streams,
                            timeout=30,  # добавляем таймаут для запроса
                        )

                        if response.status_code == 200:
                            logger.info(
                                f"Успешно импортированы трансляции для пользователя с TikTok ID: {tiktok_id}"
                            )
                        else:
                            logger.error(
                                f"Ошибка при импорте трансляций для {tiktok_id}: Статус {response.status_code}, Ответ: {response.text}"
                            )

                    except httpx.RequestError as e:
                        logger.error(
                            f"Ошибка запроса при импорте трансляций для {tiktok_id}: {str(e)}"
                        )
                    except httpx.TimeoutException:
                        logger.error(f"Таймаут при импорте трансляций для {tiktok_id}")

    except Exception as e:
        logger.error(f"Общая ошибка при импорте данных трансляций: {str(e)}")
        raise


async def import_daily_analytics(analytics_data):
    """Импорт ежедневной аналитики через API"""
    try:
        logger.info("Данные пришли из user_live_analytics")
        async with httpx.AsyncClient(verify=False) as client:
            for record in analytics_data:
                tiktok_id = record.get("tik_tok_id")

                # Получаем пользователя по TikTok ID
                user_response = await client.get(f"{API_BASE_URL}/users/{tiktok_id}")

                if user_response.status_code != 200:
                    logger.warning(
                        f"Пользователь с TikTok ID {tiktok_id} не найден, пропускаем аналитику"
                    )
                    continue

                user = user_response.json()

                # Конвертируем timestamp в объект date
                analytics_date = (
                    datetime.fromtimestamp(record["date"]).date()
                    if "date" in record
                    else date.today()
                )

                # Создаем запись аналитики
                analytics_payload = {
                    "user_id": user["id"],
                    "date": analytics_date.isoformat(),
                    "diamonds_total": record.get("diamonds_now", 0),
                    "live_duration_total": record.get("live_duration_now", 0),
                }

                logger.info(
                    f"Добавление дневной аналитики для пользователя: {user['unique_id']} на дату {analytics_date}"
                )
                analytics_response = await client.post(
                    f"{API_BASE_URL}/live/analytics", json=analytics_payload
                )

                if analytics_response.status_code in [200, 201]:
                    logger.info("Аналитика успешно добавлена")
                else:
                    logger.error(
                        f"Ошибка при добавлении аналитики: {analytics_response.status_code}"
                    )

    except Exception as e:
        logger.error(f"Ошибка при импорте дневной аналитики: {str(e)}")
        raise
