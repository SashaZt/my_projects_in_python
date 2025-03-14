import base64
from datetime import datetime, timedelta

import requests
from logger import logger
from token_storage import TokenStorage

from config import (
    APP_SCOPE,
    AUTH_URL,
    CLIENT_ID,
    CLIENT_SECRET,
    RUNAME,
    TOKEN_URL,
    USER_SCOPES,
)


class EbayAuth:
    def __init__(self, client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_storage = TokenStorage()
        self.app_token = None
        self.app_token_expiry = None
        self.user_token = None
        self.user_token_expiry = None
        self.refresh_token = self.token_storage.get_refresh_token()
        self.refresh_token_expiry = self.token_storage.get_expiry_time()

        # Пытаемся восстановить токены из хранилища
        if self.token_storage.is_access_token_valid():
            self.user_token = {"access_token": self.token_storage.get_access_token()}
            self.user_token_expiry = self.token_storage.get_expiry_time()

    def get_user_token(self, authorization_code):
        """Получение User токена через Authorization Code Grant Flow"""
        if not RUNAME:
            logger.error("RuName не настроен. Невозможно получить User токен.")
            return None

        logger.info("Запрос User токена")
        headers = {
            "Authorization": f"Basic {self._encode_credentials()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": RUNAME,
        }

        try:
            response = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()

            # Сохраняем токены в хранилище
            self.token_storage.update_tokens(token_data)

            # Сохранение токенов и сроков их действия
            self.user_token = token_data
            expires_in = token_data.get("expires_in", 7200)
            self.user_token_expiry = datetime.now() + timedelta(seconds=expires_in)

            self.refresh_token = token_data.get("refresh_token")
            refresh_token_expires_in = token_data.get("refresh_token_expires_in")
            if self.refresh_token and refresh_token_expires_in:
                self.refresh_token_expiry = datetime.now() + timedelta(
                    seconds=refresh_token_expires_in
                )

            logger.info(
                f"Получен новый User токен, действителен до: {self.user_token_expiry}"
            )
            return token_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении User токена: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Ответ сервера: {e.response.text}")
            return None

    def refresh_user_token(self):
        """Обновление User токена с помощью Refresh токена"""
        if not self.refresh_token:
            logger.error("Refresh токен отсутствует. Невозможно обновить User токен.")
            return None

        if self.refresh_token_expiry and datetime.now() > self.refresh_token_expiry:
            logger.error(
                "Refresh токен истек. Необходима повторная авторизация пользователя."
            )
            return None

        logger.info("Обновление User токена")
        headers = {
            "Authorization": f"Basic {self._encode_credentials()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {"grant_type": "refresh_token", "refresh_token": self.refresh_token}

        try:
            response = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()

            # Сохраняем токены в хранилище
            self.token_storage.update_tokens(token_data)

            # Обновление токена и срока его действия
            self.user_token = token_data
            expires_in = token_data.get("expires_in", 7200)
            self.user_token_expiry = datetime.now() + timedelta(seconds=expires_in)

            # В некоторых случаях может вернуться новый refresh_token
            new_refresh_token = token_data.get("refresh_token")
            if new_refresh_token:
                self.refresh_token = new_refresh_token
                refresh_token_expires_in = token_data.get("refresh_token_expires_in")
                if refresh_token_expires_in:
                    self.refresh_token_expiry = datetime.now() + timedelta(
                        seconds=refresh_token_expires_in
                    )

            logger.info(
                f"User токен обновлен, действителен до: {self.user_token_expiry}"
            )
            return token_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при обновлении User токена: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Ответ сервера: {e.response.text}")
            return None

    def _encode_credentials(self):
        """Кодирование учетных данных для Basic Authentication"""
        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()

    def get_application_token(self):
        """Получение Application токена через Client Credentials Grant Flow"""
        # Проверка существующего токена
        if (
            self.app_token
            and self.app_token_expiry
            and datetime.now() < self.app_token_expiry
        ):
            logger.debug("Используется существующий Application токен")
            return self.app_token

        logger.info("Запрос нового Application токена")
        headers = {
            "Authorization": f"Basic {self._encode_credentials()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {"grant_type": "client_credentials", "scope": APP_SCOPE}

        try:
            response = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()

            # Сохранение токена и срока его действия
            self.app_token = token_data
            expires_in = token_data.get(
                "expires_in", 7200
            )  # 7200 секунд (2 часа) по умолчанию
            self.app_token_expiry = datetime.now() + timedelta(seconds=expires_in)

            logger.info(
                f"Получен новый Application токен, действителен до: {self.app_token_expiry}"
            )
            return token_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении Application токена: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Ответ сервера: {e.response.text}")
            return None

    def get_authorization_url(self, scopes=None):
        """Генерация URL для авторизации пользователя (первый шаг для User токена)"""
        if not RUNAME:
            logger.error("RuName не настроен. Невозможно создать URL авторизации.")
            return None

        if not scopes:
            scopes = USER_SCOPES

        scope_str = " ".join(scopes)

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": RUNAME,
            "scope": scope_str,
            "prompt": "login",
        }

        # Формирование URL с параметрами
        query_string = "&".join(
            [
                f"{key}={requests.utils.quote(str(value))}"
                for key, value in params.items()
            ]
        )
        auth_url = f"{AUTH_URL}?{query_string}"

        logger.info(f"Сгенерирован URL авторизации: {auth_url}")
        return auth_url
