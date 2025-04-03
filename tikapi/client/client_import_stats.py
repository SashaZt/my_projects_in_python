# client_import_stats.py
import json
import asyncio
import httpx
from datetime import datetime
import sys
from pathlib import Path
from loguru import logger

# Настройка логирования
current_directory = Path.cwd()
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "tiktok_stats_import.log"
logger.add(log_file_path, level="INFO", rotation="10 MB", retention="7 days")
logger.add(sys.stderr, level="INFO")

# Базовый URL API
API_BASE_URL = "https://10.0.0.18:5000/api"

async def import_user_stats(file_path='user_info.json'):
    """Импорт статистики пользователя через API"""
    try:
        # Загружаем данные пользователя
        with open(file_path, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        tiktok_id = user_data.get('tik_tok_id')
        if not tiktok_id:
            logger.error("В данных отсутствует tik_tok_id")
            return
        
        async with httpx.AsyncClient(verify=False) as client:
            # Получаем пользователя по TikTok ID
            response = await client.get(f"{API_BASE_URL}/users/{tiktok_id}")
            
            if response.status_code != 200:
                logger.warning(f"Пользователь с TikTok ID {tiktok_id} не найден")
                return
            
            user = response.json()
            
            # Создаем статистику пользователя
            stats_payload = {
                "user_id": user['id'],
                "follower_count": user_data.get('followerCount'),
                "following_count": user_data.get('followingCount'),
                "friend_count": user_data.get('friendCount'),
                "heart_count": user_data.get('heart'),
                "video_count": user_data.get('videoCount')
            }
            
            # Проверяем, есть ли у пользователя статистика за сегодня
            today = datetime.now().date().isoformat()
            logger.info(f"Проверка статистики для пользователя: {user['unique_id']} за дату: {today}")
            
            # Получаем последнюю статистику
            try:
                stats_check = await client.get(f"{API_BASE_URL}/stats/user-stats/{user['id']}")
                
                if stats_check.status_code == 200:
                    # Проверяем, есть ли статистика за сегодня
                    stats_list = stats_check.json()
                    today_stats = None
                    
                    if stats_list:
                        # Ищем сегодняшнюю статистику
                        for stat in stats_list:
                            if 'timestamp' in stat and stat['timestamp'].startswith(today):
                                today_stats = stat
                                break
                    
                    if today_stats:
                        # Если есть статистика за сегодня, обновляем её
                        logger.info(f"Обновление существующей статистики пользователя: {user['unique_id']}")
                        stats_response = await client.put(
                            f"{API_BASE_URL}/stats/user-stats/{today_stats['id']}", 
                            json=stats_payload
                        )
                        
                        if stats_response.status_code == 200:
                            logger.info("Статистика пользователя успешно обновлена")
                        else:
                            logger.error(f"Ошибка при обновлении статистики: {stats_response.status_code}")
                    else:
                        # Если нет статистики за сегодня, создаем новую
                        logger.info(f"Добавление новой статистики для пользователя: {user['unique_id']}")
                        stats_response = await client.post(f"{API_BASE_URL}/stats/user-stats", json=stats_payload)
                        
                        if stats_response.status_code == 200:
                            logger.info("Статистика пользователя успешно добавлена")
                        else:
                            logger.error(f"Ошибка при добавлении статистики: {stats_response.status_code}")
                else:
                    # Создаем статистику, если GET запрос не удался
                    logger.info(f"Добавление первичной статистики для пользователя: {user['unique_id']}")
                    stats_response = await client.post(f"{API_BASE_URL}/stats/user-stats", json=stats_payload)
                    
                    if stats_response.status_code == 200:
                        logger.info("Статистика пользователя успешно добавлена")
                    else:
                        logger.error(f"Ошибка при добавлении статистики: {stats_response.status_code}")
            except Exception as e:
                logger.error(f"Ошибка при проверке существующей статистики: {str(e)}")
                # Пробуем просто добавить статистику
                stats_response = await client.post(f"{API_BASE_URL}/stats/user-stats", json=stats_payload)
                
                if stats_response.status_code == 200:
                    logger.info("Статистика пользователя успешно добавлена")
                else:
                    logger.error(f"Ошибка при добавлении статистики: {stats_response.status_code}")
            
            # Проверяем и обновляем никнейм если он изменился
            if user['nickname'] != user_data.get('nickname'):
                logger.info(f"Обнаружено изменение никнейма для пользователя {user['unique_id']}")
                
                # Сохраняем историю изменения никнейма
                nickname_history_payload = {
                    "user_id": user['id'],
                    "nickname": user['nickname']
                }
                
                history_response = await client.post(f"{API_BASE_URL}/stats/nickname-history", json=nickname_history_payload)
                
                if history_response.status_code == 200:
                    logger.info("История изменения никнейма успешно сохранена")
                else:
                    logger.error(f"Ошибка при сохранении истории никнейма: {history_response.status_code}")
                
                # Обновляем пользователя с новым никнеймом
                update_payload = {
                    "nickname": user_data.get('nickname')
                }
                
                update_response = await client.put(f"{API_BASE_URL}/users/{tiktok_id}", json=update_payload)
                
                if update_response.status_code == 200:
                    logger.info(f"Никнейм пользователя успешно обновлен на: {user_data.get('nickname')}")
                else:
                    logger.error(f"Ошибка при обновлении никнейма: {update_response.status_code}")
            
            # Проверяем и обновляем unique_id если он изменился
            if user['unique_id'] != user_data.get('uniqueId'):
                logger.info(f"Обнаружено изменение unique_id для пользователя {user['nickname']}")
                
                # Сохраняем историю изменения unique_id
                uniqueid_history_payload = {
                    "user_id": user['id'],
                    "unique_id": user['unique_id']
                }
                
                history_response = await client.post(f"{API_BASE_URL}/stats/uniqueid-history", json=uniqueid_history_payload)
                
                if history_response.status_code == 200:
                    logger.info("История изменения unique_id успешно сохранена")
                else:
                    logger.error(f"Ошибка при сохранении истории unique_id: {history_response.status_code}")
                
                # Обновляем пользователя с новым unique_id
                update_payload = {
                    "unique_id": user_data.get('uniqueId')
                }
                
                update_response = await client.put(f"{API_BASE_URL}/users/{tiktok_id}", json=update_payload)
                
                if update_response.status_code == 200:
                    logger.info(f"Unique_id пользователя успешно обновлен на: {user_data.get('uniqueId')}")
                else:
                    logger.error(f"Ошибка при обновлении unique_id: {update_response.status_code}")
    
    except Exception as e:
        logger.error(f"Ошибка при импорте статистики пользователя: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Запуск импорта статистики пользователя")
    try:
        asyncio.run(import_user_stats())
        logger.info("Импорт статистики пользователя завершен")
    except Exception as e:
        logger.critical(f"Критическая ошибка при импорте статистики: {str(e)}")
        sys.exit(1)