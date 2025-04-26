# ebay_auth_manager.py

import base64
import webbrowser
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

import requests
from logger import logger
from token_storage import TokenStorage

from config import AUTH_URL, CLIENT_ID, CLIENT_SECRET, RUNAME, TOKEN_URL, USER_SCOPES


class EbayAuthManager:
    def __init__(self, client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_storage = TokenStorage()
        self.user_token = None
        self.user_token_expiry = None
        self.refresh_token = self.token_storage.get_refresh_token()
        self.refresh_token_expiry = self.token_storage.get_expiry_time()

        # Инициализация токенов при создании объекта
        if self.token_storage.is_access_token_valid():
            self.user_token = self.token_storage.get_access_token()
            self.user_token_expiry = self.token_storage.get_expiry_time()
            logger.info("Восстановлен существующий токен из хранилища")
        else:
            logger.warning("Токен отсутствует или истек. Требуется обновление.")

    def _encode_credentials(self):
        """Кодирование учетных данных для заголовка Authorization."""
        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()

    def refresh_user_token(self):
        """Обновление токена доступа с использованием refresh токена."""
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

    def get_auth_url(self):
        """Генерация URL для авторизации OAuth."""
        scopes = "%20".join(USER_SCOPES)
        return f"{AUTH_URL}?client_id={self.client_id}&response_type=code&redirect_uri={RUNAME}&scope={scopes}"

    def extract_auth_code_from_url(self, auth_url):
        """Извлечение кода авторизации из URL перенаправления."""
        try:
            parsed_url = urlparse(auth_url)
            query_params = parse_qs(parsed_url.query)

            if "code" in query_params:
                auth_code = query_params["code"][0]
                logger.info(f"Извлечен код авторизации из URL")
                return auth_code
            else:
                logger.error("Код авторизации не найден в URL")
                return None
        except Exception as e:
            logger.error(f"Ошибка при извлечении кода авторизации: {str(e)}")
            return None

    def get_token_from_auth_code(self, auth_code):
        """Получение токена доступа по коду авторизации."""
        headers = {
            "Authorization": f"Basic {self._encode_credentials()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": RUNAME,
        }

        try:
            logger.info("Отправка запроса на получение токена")
            response = requests.post(TOKEN_URL, headers=headers, data=data)
            response.raise_for_status()

            token_data = response.json()
            logger.info(f"Получен ответ от сервера: {token_data}")

            # Вывод информации о токене
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 7200)
            refresh_token_expires_in = token_data.get("refresh_token_expires_in", 0)

            expiry_date = datetime.now() + timedelta(seconds=expires_in)
            refresh_expiry_date = datetime.now() + timedelta(
                seconds=refresh_token_expires_in
            )

            # Обновление свойств объекта
            self.user_token = access_token
            self.user_token_expiry = expiry_date
            self.refresh_token = refresh_token
            self.refresh_token_expiry = refresh_expiry_date

            # Сохранение токена в хранилище
            self.token_storage.update_tokens(token_data)
            logger.info("Токен успешно сохранен в хранилище")

            return token_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении токена: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Ответ сервера: {e.response.text}")
            return None

    def authenticate(self):
        """Проверка и обновление токена при необходимости."""
        # Проверка наличия действительного токена
        if self.token_storage.is_access_token_valid():
            logger.info("Найден действительный токен доступа")
            self.user_token = self.token_storage.get_access_token()
            self.user_token_expiry = self.token_storage.get_expiry_time()
            return self.user_token

        # Попытка обновления токена
        if self.refresh_token:
            logger.info("Попытка обновления токена с помощью refresh токена")
            token_data = self.refresh_user_token()
            if token_data:
                logger.info("Токен успешно обновлен")
                return token_data.get("access_token")

        # Если не удалось обновить токен, запрашиваем новую авторизацию
        logger.info("Требуется новая авторизация")
        return self.request_new_authorization()

    def request_new_authorization(self):
        """Запрос новой авторизации и получение токена."""
        print("\n=== Требуется авторизация в eBay API ===")
        print("Будет сгенерирована ссылка для авторизации.")

        # Генерация URL для авторизации
        auth_url = self.get_auth_url()
        print(f"\nСсылка для авторизации:\n{auth_url}")

        # Открытие браузера с URL для авторизации
        print("\nПытаемся открыть браузер автоматически...")
        try:
            webbrowser.open(auth_url)
            print("Браузер открыт. Пожалуйста, авторизуйтесь в eBay.")
        except Exception as e:
            print(f"Не удалось открыть браузер автоматически: {e}")
            print("Пожалуйста, скопируйте ссылку и откройте ее в браузере вручную.")

        # Запрос URL-перенаправления с кодом авторизации
        print("\nПосле авторизации вы будете перенаправлены на страницу.")
        print("Скопируйте полный URL из адресной строки браузера и вставьте его ниже:")

        redirect_url = input("> ")

        # Извлечение кода авторизации из URL
        auth_code = self.extract_auth_code_from_url(redirect_url)

        if auth_code:
            print(f"Извлеченный код авторизации: {auth_code[:15]}...")

            # Получение токена по коду авторизации
            token_data = self.get_token_from_auth_code(auth_code)

            if token_data:
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in", 7200)
                refresh_token_expires_in = token_data.get("refresh_token_expires_in", 0)

                expiry_date = datetime.now() + timedelta(seconds=expires_in)
                refresh_expiry_date = datetime.now() + timedelta(
                    seconds=refresh_token_expires_in
                )

                print(f"\n✅ Токен доступа получен!")
                print(
                    f"Токен доступа: {access_token[:15]}... (длина: {len(access_token)})"
                )
                print(
                    f"Refresh токен: {refresh_token[:15]}... (длина: {len(refresh_token)})"
                )
                print(f"Токен действителен до: {expiry_date}")
                print(f"Refresh токен действителен до: {refresh_expiry_date}")

                return access_token
            else:
                print("\n❌ Не удалось получить токен по коду авторизации.")
                return None
        else:
            print("\n❌ Не удалось извлечь код авторизации из URL.")
            return None


def main():
    """Основная функция для проверки работы аутентификации."""
    print("=== Менеджер аутентификации eBay API ===")

    auth_manager = EbayAuthManager()

    # Попытка аутентификации
    token = auth_manager.authenticate()

    if token:
        print("\n✅ Аутентификация успешна!")
        print(f"Текущий токен: {token[:15]}...")
        print(f"Токен действителен до: {auth_manager.user_token_expiry}")

        if auth_manager.refresh_token:
            print(f"Refresh токен: {auth_manager.refresh_token[:15]}...")
            print(f"Refresh токен действителен до: {auth_manager.refresh_token_expiry}")
    else:
        print("\n❌ Аутентификация не удалась.")


if __name__ == "__main__":
    main()
