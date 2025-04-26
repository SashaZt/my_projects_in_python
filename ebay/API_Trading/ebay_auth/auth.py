import base64
from datetime import datetime, timedelta

import requests
from logger import logger
from token_storage import TokenStorage

from config import AUTH_URL, CLIENT_ID, CLIENT_SECRET, RUNAME, TOKEN_URL, USER_SCOPES


class EbayAuth:
    def __init__(self, client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_storage = TokenStorage()
        self.user_token = None
        self.user_token_expiry = None
        self.refresh_token = self.token_storage.get_refresh_token()
        self.refresh_token_expiry = self.token_storage.get_expiry_time()

        if self.token_storage.is_access_token_valid():
            self.user_token = self.token_storage.get_access_token()
            self.user_token_expiry = self.token_storage.get_expiry_time()
            logger.info("Восстановлен существующий токен из хранилища")
        else:
            logger.warning("Токен отсутствует или истек. Требуется обновление.")

    def _encode_credentials(self):
        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()

    def refresh_user_token(self):
        if not self.refresh_token:
            logger.error("Refresh токен отсутствует.")
            return None

        if self.refresh_token_expiry and datetime.now() > self.refresh_token_expiry:
            logger.error("Refresh токен истек. Требуется повторная авторизация.")
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
            logger.info(f"Получен новый токен: {token_data}")
            self.token_storage.update_tokens(token_data)
            self.user_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 7200)
            self.user_token_expiry = datetime.now() + timedelta(seconds=expires_in)
            logger.info(
                f"User токен обновлен, действителен до: {self.user_token_expiry}"
            )
            return token_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при обновлении токена: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Ответ сервера: {e.response.text}")
            return None
