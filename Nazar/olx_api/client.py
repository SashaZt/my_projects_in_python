import requests
import webbrowser
import uuid

SERVER_URL = "https://185.233.116.213:5000"
CALLBACK_URL = f"{SERVER_URL}/auth/connect"
CERT_PATH = "server.crt"  # Укажите путь к вашему сертификату


def get_auth_url():
    """
    Генерирует URL для авторизации и возвращает URL вместе с state.
    """
    state = str(uuid.uuid4())  # Генерация динамического UUID для state
    auth_url = (
        f"https://www.olx.ua/oauth/authorize/"
        f"?client_id=202045"
        f"&response_type=code"
        f"&state={state}"
        f"&scope=read+write+v2"
        f"&redirect_uri=https://185.233.116.213:5000/auth/connect"
    )
    return auth_url, state


def main():
    # 1. Получаем URL для авторизации
    auth_url, state = get_auth_url()
    if not auth_url or not state:
        print("Не удалось получить URL для авторизации")
        return

    print(f"Перейдите по ссылке для авторизации: {auth_url}")
    webbrowser.open(auth_url)

    # 2. Ожидание авторизации
    code = input("Введите `code`: ").strip()

    # 3. Отправляем `code` и `state` на сервер
    response = requests.get(
        CALLBACK_URL, params={"code": code, "state": state}, verify=CERT_PATH
    )
    if response.status_code == 200:
        print("Токен успешно получен:", response.json())
    else:
        print("Ошибка получения токена:", response.text)


if __name__ == "__main__":
    main()
