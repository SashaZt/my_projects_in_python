import base64
import json
import sys
from pathlib import Path

import requests
from logger import logger

# Настройка путей и директорий
current_directory = Path.cwd()
data_directory = current_directory / "data"
config_directory = current_directory / "config"
data_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)

# Пути к файлам
config_json_file = config_directory / "config.json"
access_token_json_file = data_directory / "access_token.json"


def load_product_data(file_path):
    """Загрузка данных из JSON файла"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных из {file_path}: {e}")
        return None


def save_json_data(data, file_path):
    """Сохранение данных в JSON файл"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в файл {file_path}: {e}")
        return False


# Загрузка конфигурации
def load_config():
    """Загрузка конфигурации из файла"""
    config = load_product_data(config_json_file)
    if not config:
        logger.error(f"Не удалось загрузить конфигурацию из {config_json_file}")
        return None
    return config.get("rozetka", {})


def get_auth_token():
    """Авторизация и получение токена"""
    # Загружаем конфигурацию
    config = load_config()
    if not config:
        return None

    username = config.get("USERNAME")
    password = config.get("PASSWORD")

    if not username or not password:
        logger.error("Отсутствуют данные для авторизации в конфигурационном файле")
        return None

    url = "https://api-seller.rozetka.com.ua/sites"

    try:
        # Кодируем пароль в base64
        password_base64 = base64.b64encode(password.encode()).decode()

        payload = {"username": username, "password": password_base64}
        headers = {"Content-Type": "application/json"}

        logger.info("Запрос нового токена авторизации...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if data.get("success"):
            token = data["content"]["access_token"]
            logger.info("Токен успешно получен")

            # Обновляем токен в конфигурации
            config["TOKEN_ROZETKA"] = token

            # Обновляем основной конфиг
            full_config = load_product_data(config_json_file) or {}
            full_config["rozetka"] = config

            # Сохраняем обновленный конфиг
            save_json_data(full_config, config_json_file)

            # # Также сохраняем токен в отдельный файл для совместимости
            # save_json_data(token, access_token_json_file)

            return token
        else:
            error_msg = data.get("errors", {}).get("message", "Неизвестная ошибка")
            logger.error(f"Ошибка авторизации: {error_msg}")
            return None
    except Exception as e:
        logger.error(f"Ошибка при получении токена: {e}")
        return None


def validyty_token():
    """Проверка валидности токена и его обновление при необходимости"""
    # Загружаем конфигурацию
    config = load_config()
    if not config:
        return None

    token = config.get("TOKEN_ROZETKA")

    # Если токен не найден, получаем новый
    if not token:
        logger.warning("Токен не найден в конфигурации, получаем новый...")
        return get_auth_token()

    # Проверяем токен на валидность, делая тестовый запрос
    # logger.info("Проверка валидности токена...")
    count_new_url = "https://api-seller.rozetka.com.ua/orders/counts-new"
    count_new_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        test_response = requests.get(
            count_new_url, headers=count_new_headers, timeout=10
        )
        test_data = test_response.json()

        # Проверяем успешность запроса и наличие ошибок, связанных с токеном
        if (
            not test_data.get("success")
            or test_data.get("errors", {}).get("message") == "incorrect_access_token"
        ):
            logger.warning("Токен недействителен, получаем новый...")
            return get_auth_token()
        else:
            logger.info("Токен валидный")
            return token
    except Exception as e:
        logger.warning(f"Ошибка при проверке токена: {e}, получаем новый...")
        return get_auth_token()


# Функция для получения токена (используется в других модулях)
def get_token():
    """Получение токена для API запросов"""
    # Сначала пробуем загрузить из конфигурации
    config = load_config()
    if config and config.get("TOKEN_ROZETKA"):
        return config["TOKEN_ROZETKA"]

    # Если не удалось, пробуем загрузить из файла токена
    token = load_product_data(access_token_json_file)
    if token:
        return token

    # Если и это не удалось, получаем новый токен
    return get_auth_token()


# Если скрипт запускается напрямую, проверяем и обновляем токен
if __name__ == "__main__":
    token = validyty_token()
    if token:
        logger.info(f"Токен: {token}")
    else:
        logger.error("Не удалось получить или проверить токен")
