import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import requests
from logger import logger


class KazPostAuthManager:
    """
    Класс для управления авторизацией и токенами KazPost API
    """

    def __init__(
        self,
        username: str,
        password: str,
        auth_url: str = "https://open.post.kz/npi-integration/api/auth/login",
        token_file: str = "kazpost_token.json",
    ):
        """
        Инициализация менеджера авторизации

        :param username: Имя пользователя для API
        :param password: Пароль для API
        :param auth_url: URL для авторизации
        :param token_file: Путь к файлу для сохранения токена
        """
        self.username = username
        self.password = password
        self.auth_url = auth_url
        self.token_file = token_file
        self.access_token = None
        self.token_expiry = None

        # Пытаемся загрузить токен из файла при инициализации
        self.load_token()

    def load_token(self) -> bool:
        """
        Загрузка токена из файла

        :return: True если токен успешно загружен и валиден, иначе False
        """
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, "r") as f:
                    token_data = json.load(f)

                # Получаем данные токена
                self.access_token = token_data.get("accessToken")
                expiry_timestamp = token_data.get("expiry")

                # Если есть время истечения, проверяем его
                if expiry_timestamp:
                    self.token_expiry = datetime.fromtimestamp(expiry_timestamp)

                    # Проверяем, не истек ли токен
                    if self.token_expiry > datetime.now() + timedelta(minutes=5):
                        logger.info("Токен успешно загружен из файла")
                        return True
                    else:
                        logger.info("Загруженный токен истек или скоро истечет")
                        return False
                else:
                    logger.warning("В файле токена отсутствует время истечения")
                    return False
            else:
                logger.info("Файл токена не найден")
                return False
        except Exception as e:
            logger.error(f"Ошибка при загрузке токена: {str(e)}")
            return False

    def save_token(self, token_data: Dict) -> None:
        """
        Сохранение токена в файл

        :param token_data: Данные токена для сохранения
        """
        try:
            # Добавляем время истечения токена (примерно 1 час от текущего времени)
            token_data["expiry"] = (datetime.now() + timedelta(hours=1)).timestamp()

            # Сохраняем токен в файл
            with open(self.token_file, "w") as f:
                json.dump(token_data, f)

            logger.info("Токен успешно сохранен в файл")
        except Exception as e:
            logger.error(f"Ошибка при сохранении токена: {str(e)}")

    def authenticate(self) -> Tuple[bool, str]:
        """
        Выполнение аутентификации и получение нового токена

        :return: Кортеж (успешно/неуспешно, сообщение)
        """
        try:
            # Подготавливаем данные для авторизации
            auth_data = {"username": self.username, "password": self.password}

            # Подготавливаем заголовки
            headers = {"Content-Type": "application/json"}

            # Отправляем запрос на авторизацию
            response = requests.post(
                self.auth_url, json=auth_data, headers=headers, timeout=30
            )

            # Проверяем ответ
            if response.status_code == 200:
                token_data = response.json()

                # Сохраняем токен в атрибуты класса
                self.access_token = token_data.get("accessToken")
                self.token_expiry = datetime.now() + timedelta(hours=1)

                # Сохраняем токен в файл
                self.save_token(token_data)

                logger.info("Успешная аутентификация")
                return True, "Аутентификация успешна"
            else:
                error_msg = (
                    f"Ошибка аутентификации: {response.status_code}, {response.text}"
                )
                logger.error(error_msg)
                return False, error_msg
        except Exception as e:
            error_msg = f"Исключение при аутентификации: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_token(self, force_refresh: bool = False) -> Optional[str]:
        """
        Получение действующего токена, при необходимости с обновлением

        :param force_refresh: Принудительно запросить новый токен
        :return: Действующий токен или None при ошибке
        """
        # Проверяем, нужно ли обновить токен
        if (
            force_refresh
            or not self.access_token
            or not self.token_expiry
            or self.token_expiry <= datetime.now() + timedelta(minutes=5)
        ):
            success, _ = self.authenticate()
            if not success:
                return None

        return self.access_token

    def get_auth_header(self) -> Dict[str, str]:
        """
        Получение заголовка авторизации для API запросов

        :return: Словарь с заголовком авторизации
        """
        token = self.get_token()
        if token:
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        return {"Content-Type": "application/json"}

    def execute_with_auth(self, request_func, *args, **kwargs):
        """
        Выполнение запроса с авторизацией и автоматическим обновлением токена при необходимости

        :param request_func: Функция для выполнения запроса
        :param args: Позиционные аргументы для функции запроса
        :param kwargs: Именованные аргументы для функции запроса
        :return: Результат выполнения функции запроса
        """
        # Получаем токен и заголовки авторизации
        auth_headers = self.get_auth_header()

        # Если заголовки уже переданы, объединяем их
        if "headers" in kwargs:
            kwargs["headers"].update(auth_headers)
        else:
            kwargs["headers"] = auth_headers

        # Выполняем запрос
        response = request_func(*args, **kwargs)

        # Проверяем, требуется ли обновление токена (код 401)
        if hasattr(response, "status_code") and response.status_code == 401:
            logger.info("Токен недействителен, получаем новый")

            # Повторно аутентифицируемся
            success, _ = self.authenticate()
            if success:
                # Обновляем заголовки с новым токеном
                auth_headers = self.get_auth_header()
                if "headers" in kwargs:
                    kwargs["headers"].update(auth_headers)
                else:
                    kwargs["headers"] = auth_headers

                # Повторяем запрос
                response = request_func(*args, **kwargs)

        return response


# Пример использования
if __name__ == "__main__":

    # Создаем менеджер авторизации
    auth_manager = KazPostAuthManager(
        username="ainagul0101@post.kz", password="Venatura0103!"
    )

    # Пример выполнения запроса с авторизацией
    def make_test_request(url, **kwargs):
        return requests.get(url, **kwargs)

    # Выполняем запрос с автоматической авторизацией
    response = auth_manager.execute_with_auth(
        make_test_request, "https://open.post.kz/npi-integration/api/some-endpoint"
    )

    logger.info(f"Статус ответа: {response.status_code}")
    logger.info(f"Ответ: {response.text}")
