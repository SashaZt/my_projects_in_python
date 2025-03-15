import json
import os
from datetime import datetime, timedelta
from config import BASE_URL


class TokenStorage:
    def __init__(self, file_path="config/tokens.json"):
        self.file_path = file_path
        self.tokens = self._load_tokens()
        self.base_url = BASE_URL

    def _load_tokens(self):
        """Загрузка токенов из файла"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка при загрузке токенов: {e}")
                return {}
        return {}

    def save_tokens(self, tokens):
        """Сохранение токенов в файл"""
        # Создание директории, если она не существует
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        # Сохранение токенов в файл
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2)

    def get_access_token(self):
        """Получение access token"""
        return self.tokens.get("access_token")

    def get_refresh_token(self):
        """Получение refresh token"""
        return self.tokens.get("refresh_token")

    def get_expiry_time(self):
        """Получение времени истечения токена"""
        if "expires_at" in self.tokens:
            return datetime.fromisoformat(self.tokens["expires_at"])
        return None

    def is_access_token_valid(self):
        """Проверка валидности access token"""
        expiry_time = self.get_expiry_time()
        if not expiry_time:
            return False

        # Проверяем, что токен действителен еще как минимум 5 минут
        return expiry_time > datetime.now() + timedelta(minutes=5)

    def update_tokens(self, token_data):
        """Обновление токенов"""
        # Сохраняем токены
        self.tokens = {
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get(
                "refresh_token", self.tokens.get("refresh_token")
            ),
            "expires_in": token_data.get("expires_in"),
            "expires_at": (
                datetime.now() + timedelta(seconds=token_data.get("expires_in", 7200))
            ).isoformat(),
            "refresh_token_expires_in": token_data.get(
                "refresh_token_expires_in", self.tokens.get("refresh_token_expires_in")
            ),
            "refresh_token_expires_at": (
                (
                    datetime.now()
                    + timedelta(seconds=token_data.get("refresh_token_expires_in", 0))
                ).isoformat()
                if token_data.get("refresh_token_expires_in")
                else self.tokens.get("refresh_token_expires_at")
            ),
        }

        # Сохраняем токены в файл
        self.save_tokens(self.tokens)

        return self.tokens

    def get_base_url(self):
        """Получение базового URL для API"""
        return self.base_url
