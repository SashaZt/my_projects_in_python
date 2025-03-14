import base64
import json

import requests

# Учетные данные (из вашего сообщения)
CLIENT_ID = "RESTEQsp-al-SBX-0ded19238-d461cb8d"
CLIENT_SECRET = "SBX-ded19238822e-de02-4680-a30a-83bc"
DEV_ID = "3c0ac2c6-23a2-4ff4-aa2a-6d5a163ffdb9"

# Endpoints для Sandbox среды
TOKEN_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

# Scope для Application токена (для примера - базовый scope)
APP_SCOPE = "https://api.ebay.com/oauth/api_scope"


def get_application_token():
    """Получение Application токена через Client Credentials Grant Flow"""

    # Кодирование учетных данных для Basic Authentication
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {"grant_type": "client_credentials", "scope": APP_SCOPE}

    try:
        response = requests.post(TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()  # Проверка на ошибки HTTP
        token_data = response.json()

        print("Токен успешно получен!")
        return token_data
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении токена: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Ответ сервера: {e.response.text}")
        return None


# Функция для тестового вызова API
def test_api_call(token):
    """Тестовый вызов API с использованием полученного токена"""
    if not token:
        print("Токен не получен, невозможно выполнить вызов API")
        return

    # Пример API endpoint
    api_url = "https://api.sandbox.ebay.com/commerce/taxonomy/v1/get_default_category_tree_id?marketplace_id=EBAY_DE"

    headers = {
        "Authorization": f'Bearer {token["access_token"]}',
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        print("API вызов успешен:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при вызове API: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Ответ сервера: {e.response.text}")
        return None


# Основной код
if __name__ == "__main__":
    print("Получение Application токена...")
    token_data = get_application_token()

    if token_data:
        print(f"Токен действителен до: {token_data.get('expires_in')} секунд")

        # Тестовый вызов API
        print("\nВыполнение тестового вызова API...")
        test_api_call(token_data)
