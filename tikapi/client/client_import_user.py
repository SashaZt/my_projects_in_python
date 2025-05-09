# client_import_user.py
import json
import sys
from pathlib import Path

import httpx
from config.config import API_BASE_URL, USER_JSON_FILE
from config.logger import logger


async def import_user_data(user_datas):
    """Импорт данных пользователя через API"""
    try:

        # Загружаем список пользователей для получения account_key
        with open(USER_JSON_FILE, "r", encoding="utf-8") as f:
            users_list = json.load(f)
        logger.info("Пришло")
        logger.info(user_datas)
        for user_data in user_datas:
            # Находим account_key для данного TikTok ID
            tiktok_id = user_data.get("tik_tok_id")
            account_key = None

            for user in users_list:
                if user.get("tik_tok_id") == tiktok_id:
                    account_key = user.get("account_key")
                    logger.info(f"Найден account_key: {account_key}")
                    break

            # Формируем данные пользователя
            user_payload = {
                "tik_tok_id": tiktok_id,
                "account_key": account_key,
                "nickname": user_data.get("nickname"),
                "unique_id": user_data.get("uniqueId"),
                "avatar_medium": user_data.get("avatarMedium"),
                "following_visibility": user_data.get("followingVisibility"),
                "is_under_age_18": user_data.get("isUnderAge18"),
                "open_favorite": user_data.get("openFavorite"),
                "private_account": user_data.get("privateAccount"),
                "signature": user_data.get("signature"),
            }

            async with httpx.AsyncClient(verify=False) as client:
                # Проверяем существование пользователя
                response = await client.get(f"{API_BASE_URL}/users/{tiktok_id}")
                user_exists = response.status_code == 200

                # Создаем или обновляем пользователя
                if user_exists:
                    logger.info(f"Обновление пользователя: {user_data.get('uniqueId')}")
                    response = await client.put(
                        f"{API_BASE_URL}/users/{tiktok_id}", json=user_payload
                    )
                else:
                    logger.info(f"Создание пользователя: {user_data.get('uniqueId')}")
                    response = await client.post(
                        f"{API_BASE_URL}/users/", json=user_payload
                    )

                if response.status_code == 200:
                    logger.info(
                        f"Пользователь успешно {'обновлен' if user_exists else 'создан'}"
                    )
                    # Статистика будет добавлена отдельным скриптом
                    logger.info(
                        f"Для добавления статистики запустите client_import_stats.py"
                    )
                else:
                    logger.error(
                        f"Ошибка при обработке пользователя: {response.status_code}"
                    )

    except Exception as e:
        logger.error(f"Ошибка при импорте данных пользователя: {str(e)}")
        raise


async def import_all_users(users_data):
    """Импорт всех пользователей из users.json"""
    try:
        async with httpx.AsyncClient(verify=False) as client:
            for user_data in users_data:
                tiktok_id = user_data.get("tik_tok_id")
                username = user_data.get("username")

                if not tiktok_id or not username:
                    logger.warning(f"Пропуск записи пользователя с неполными данными")
                    continue

                # Проверяем существование пользователя
                response = await client.get(f"{API_BASE_URL}/users/{tiktok_id}")

                if response.status_code == 200:
                    logger.info(f"Пользователь {username} уже существует")
                    continue  # Переходим к следующему пользователю

                # Создаем пользователя
                user_payload = {
                    "tik_tok_id": tiktok_id,
                    "account_key": user_data.get("account_key"),
                    "unique_id": username,
                    "nickname": username,
                }

                logger.info(f"Создание пользователя: {username}")
                response = await client.post(
                    f"{API_BASE_URL}/users/", json=user_payload
                )

                if response.status_code in [200, 201]:
                    logger.info(f"Пользователь {username} успешно создан")
                else:
                    logger.error(
                        f"Ошибка при создании пользователя: {response.status_code}"
                    )

    except Exception as e:
        logger.error(f"Ошибка при импорте всех пользователей: {str(e)}")
        raise
