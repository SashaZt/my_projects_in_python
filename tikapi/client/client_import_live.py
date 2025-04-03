# client_import_live.py
import json
import asyncio
import httpx
from datetime import datetime, date
import sys
from pathlib import Path
from loguru import logger

# Настройка логирования
current_directory = Path.cwd()
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "tiktok_live_import.log"
logger.add(log_file_path, level="INFO", rotation="10 MB", retention="7 days")
logger.add(sys.stderr, level="INFO")

# Базовый URL API
API_BASE_URL = "https://10.0.0.18:5000/api"  # Используем HTTP вместо HTTPS

async def import_live_streams(file_path='live_streams.json'):
    """Импорт данных трансляций через API"""
    try:
        # Загружаем данные трансляций
        with open(file_path, 'r', encoding='utf-8') as f:
            live_data = json.load(f)
        
        async with httpx.AsyncClient(verify=False) as client:
            # Обрабатываем трансляции по каждому пользователю
            for tiktok_id, streams in live_data.items():
                logger.info(f"Импорт {len(streams)} трансляций для пользователя с TikTok ID: {tiktok_id}")
                
                # Используем эндпоинт массового импорта
                response = await client.post(
                    f"{API_BASE_URL}/live/import-bulk",
                    params={"tiktok_id": tiktok_id},
                    json=streams
                )
                
                if response.status_code == 200:
                    logger.info(f"Успешно импортированы трансляции для пользователя с TikTok ID: {tiktok_id}")
                else:
                    logger.error(f"Ошибка при импорте трансляций: {response.status_code}")
    
    except Exception as e:
        logger.error(f"Ошибка при импорте данных трансляций: {str(e)}")
        raise

async def import_daily_analytics(file_path='user_live_analytics.json'):
    """Импорт ежедневной аналитики через API"""
    try:
        # Загружаем данные аналитики
        with open(file_path, 'r', encoding='utf-8') as f:
            analytics_data = json.load(f)
        
        async with httpx.AsyncClient(verify=False) as client:
            for record in analytics_data:
                tiktok_id = record.get('tik_tok_id')
                
                # Получаем пользователя по TikTok ID
                user_response = await client.get(f"{API_BASE_URL}/users/{tiktok_id}")
                
                if user_response.status_code != 200:
                    logger.warning(f"Пользователь с TikTok ID {tiktok_id} не найден, пропускаем аналитику")
                    continue
                
                user = user_response.json()
                
                # Конвертируем timestamp в объект date
                analytics_date = datetime.fromtimestamp(record['date']).date() if 'date' in record else date.today()
                
                # Создаем запись аналитики
                analytics_payload = {
                    "user_id": user['id'],
                    "date": analytics_date.isoformat(),
                    "diamonds_total": record.get('diamonds_now', 0),
                    "live_duration_total": record.get('live_duration_now', 0)
                }
                
                logger.info(f"Добавление дневной аналитики для пользователя: {user['unique_id']} на дату {analytics_date}")
                analytics_response = await client.post(f"{API_BASE_URL}/live/analytics", json=analytics_payload)
                
                if analytics_response.status_code in [200, 201]:
                    logger.info(f"Аналитика успешно добавлена")
                else:
                    logger.error(f"Ошибка при добавлении аналитики: {analytics_response.status_code}")
    
    except Exception as e:
        logger.error(f"Ошибка при импорте дневной аналитики: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Запуск импорта данных трансляций")
    try:
        asyncio.run(import_live_streams())
        asyncio.run(import_daily_analytics())
        logger.info("Импорт данных трансляций завершен")
    except Exception as e:
        logger.critical(f"Критическая ошибка при импорте данных: {str(e)}")
        sys.exit(1)