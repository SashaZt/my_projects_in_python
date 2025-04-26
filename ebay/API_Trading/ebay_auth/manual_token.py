# manual_token.py

import base64
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

import requests
from logger import logger
from token_storage import TokenStorage

from config import CLIENT_ID, CLIENT_SECRET, RUNAME, TOKEN_URL


def extract_auth_code_from_url(auth_url):
    """Извлечение кода авторизации из URL перенаправления."""
    try:
        # Парсинг URL и извлечение параметров запроса
        parsed_url = urlparse(auth_url)
        query_params = parse_qs(parsed_url.query)

        # Извлечение кода авторизации
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


def get_token_from_auth_code(auth_code):
    """Получение токена по коду авторизации."""
    # Формирование заголовков запроса
    auth_string = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_string}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # Формирование данных запроса
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": RUNAME,
    }

    try:
        # Выполнение запроса на получение токена
        logger.info("Отправка запроса на получение токена")
        response = requests.post(TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()

        # Обработка ответа
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

        print(f"\nТокен доступа получен!")
        print(f"Токен доступа: {access_token[:15]}... (длина: {len(access_token)})")
        print(f"Refresh токен: {refresh_token[:15]}... (длина: {len(refresh_token)})")
        print(f"Токен действителен до: {expiry_date}")
        print(f"Refresh токен действителен до: {refresh_expiry_date}")

        # Сохранение токена в хранилище
        token_storage = TokenStorage()
        token_storage.update_tokens(token_data)
        logger.info("Токен успешно сохранен в хранилище")

        return token_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении токена: {e}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Ответ сервера: {e.response.text}")
        return None


def main():
    print("=== Ручное получение токена eBay API ===")
    print("\nВведите полный URL после авторизации (содержащий параметр code):")
    print(
        "Пример: https://auth.ebay.com/oauth2/authorize?isAuthSuccessful=true&code=abc123..."
    )

    # Для удобства, можно закомментировать строку ниже и раскомментировать строку с вашим URL
    auth_url = input("> ")
    # auth_url = "https://auth2.ebay.com/oauth2/ThirdPartyAuthSucessFailure?isAuthSuccessful=true&code=v%5E1.1%23i%5E1%23r%5E1%23p%5E3%23f%5E0%23I%5E3%23t%5EUl41XzExOjNFMTUyODM3QzIyN0YyNDk3OEQ3MTEyRkY1MTUxNDFFXzBfMSNFXjEyODQ%3D&expires_in=299"

    # Извлечение кода авторизации
    auth_code = extract_auth_code_from_url(auth_url)

    if auth_code:
        print(f"Извлеченный код авторизации: {auth_code[:15]}...")

        # Получение токена по коду авторизации
        token_data = get_token_from_auth_code(auth_code)

        if token_data:
            print("\n✅ Токен успешно получен и сохранен!")
        else:
            print("\n❌ Не удалось получить токен по коду авторизации.")
    else:
        print("\n❌ Не удалось извлечь код авторизации из URL.")


if __name__ == "__main__":
    main()
