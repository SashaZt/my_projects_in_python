# api_connection_test.py
import json

import requests
from auth import EbayAuth
from logger import logger


def test_api_connection():
    """Проверка соединения с API eBay и статуса токенов"""
    logger.info("Начинаем проверку соединения с API eBay")

    # Инициализируем авторизацию
    auth = EbayAuth()

    # 1. Проверка получения Application токена
    logger.info("1. Проверка получения Application токена...")
    app_token = auth.get_application_token()
    if app_token:
        logger.info("✅ Application токен успешно получен")
        logger.debug(f"Срок действия: {auth.app_token_expiry}")
    else:
        logger.error("❌ Не удалось получить Application токен")
        return False

    # 2. Проверка базового эндпоинта (который не требует специальных прав)
    logger.info("2. Проверка базового эндпоинта...")
    try:
        headers = {
            "Authorization": f"Bearer {app_token['access_token']}",
            "Content-Type": "application/json",
        }
        response = requests.get(
            f"{auth.token_storage.get_base_url()}/commerce/taxonomy/v1/get_default_category_tree_id?marketplace_id=EBAY_DE",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        logger.info(f"✅ Базовый эндпоинт доступен, ответ: {response.json()}")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке базового эндпоинта: {e}")
        return False

    # 3. Проверка User токена (если есть)
    logger.info("3. Проверка User токена...")
    if auth.user_token:
        logger.info("✅ User токен найден в хранилище")
        logger.debug(f"Срок действия: {auth.user_token_expiry}")

        # Проверка эндпоинта, требующего User токен
        try:
            headers = {
                "Authorization": f"Bearer {auth.user_token['access_token']}",
                "Content-Type": "application/json",
            }
            response = requests.get(
                f"{auth.token_storage.get_base_url()}/sell/account/v1/privilege",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            logger.info(
                f"✅ Эндпоинт с User токеном доступен, ответ: {response.json()}"
            )
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке эндпоинта с User токеном: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Код ошибки: {e.response.status_code}")
                logger.error(f"Ответ сервера: {e.response.text}")

            # Если токен устарел, пробуем обновить
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
                and auth.refresh_token
            ):
                logger.info("Попытка обновления User токена...")
                refreshed_token = auth.refresh_user_token()
                if refreshed_token:
                    logger.info("✅ User токен успешно обновлен")
                else:
                    logger.error("❌ Не удалось обновить User токен")
                    return False
    else:
        logger.warning(
            "⚠️ User токен не найден. Для работы с Inventory API необходим User токен."
        )
        logger.info("Запуск процесса получения User токена...")

        # Генерация URL для авторизации
        auth_url = auth.get_authorization_url()
        if auth_url:
            logger.info(f"Для получения User токена перейдите по следующей ссылке:")
            logger.info(auth_url)
            logger.info("После авторизации вы будете перенаправлены на указанный URL.")
            logger.info("Скопируйте код авторизации из URL и введите его ниже:")

            auth_code = input("Введите код авторизации: ")
            if auth_code:
                token_data = auth.get_user_token(auth_code)
                if token_data:
                    logger.info("✅ User токен успешно получен")
                else:
                    logger.error("❌ Не удалось получить User токен")
                    return False
        else:
            logger.error("❌ Не удалось сгенерировать URL для авторизации")
            return False

    # 4. Проверка доступа к Inventory API
    logger.info("4. Проверка доступа к Inventory API...")
    try:
        headers = {
            "Authorization": f"Bearer {auth.user_token['access_token']}",
            "Content-Type": "application/json",
        }
        response = requests.get(
            f"{auth.token_storage.get_base_url()}/sell/inventory/v1/inventory_item",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        logger.info(f"✅ Inventory API доступен, ответ: {response.json()}")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке доступа к Inventory API: {e}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Код ошибки: {e.response.status_code}")
            logger.error(f"Ответ сервера: {e.response.text}")
        return False

    logger.info("Проверка соединения с API eBay завершена успешно")
    return True


if __name__ == "__main__":
    test_api_connection()
