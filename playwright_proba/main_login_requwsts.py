import json
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def login_and_save_page(username, password, target_url, output_file=None, debug=True):
    """
    Авторизуется на сайте с помощью requests и сохраняет HTML-страницу по указанному URL

    Args:
        username (str): Логин для авторизации
        password (str): Пароль для авторизации
        target_url (str): URL страницы для сохранения
        output_file (str, optional): Путь для сохранения HTML. Если None, генерируется автоматически.
        debug (bool): Режим отладки

    Returns:
        tuple: (успех операции (bool), путь к сохраненному файлу или сообщение об ошибке)
    """
    try:
        # Создаем сессию
        session = requests.Session()

        # Устанавливаем User-Agent как в браузере
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Шаг 1: Получаем главную страницу для установки начальных куки
        print("Шаг 1: Получение начальных куки...")
        initial_response = session.get("https://www.ziva-fitness.com/", headers=headers)
        if debug:
            print(f"Начальные куки: {session.cookies.get_dict()}")

        # Шаг 2: Загружаем страницу логина
        print("Шаг 2: Загрузка страницы логина...")
        login_page_response = session.get(
            "https://www.ziva-fitness.com/login/", headers=headers
        )

        if login_page_response.status_code != 200:
            return (
                False,
                f"Не удалось загрузить страницу логина. Код ответа: {login_page_response.status_code}",
            )

        if debug:
            print(f"Куки после загрузки страницы логина: {session.cookies.get_dict()}")

        # Шаг 3: Анализируем форму логина для извлечения информации
        soup = BeautifulSoup(login_page_response.text, "html.parser")

        # Поиск form_id
        form = soup.select_one("form")
        if not form:
            return False, "Не удалось найти форму логина на странице"

        # Поиск ID полей для логина и пароля
        inputs = soup.select("input")

        login_id = None
        password_id = None
        remember_id = None

        for input_field in inputs:
            input_type = input_field.get("type", "")
            input_id = input_field.get("id", "")

            if input_type == "text" or input_type == "email":
                login_id = input_id
            elif input_type == "password":
                password_id = input_id
            elif input_type == "checkbox":
                remember_id = input_id

        if not login_id or not password_id:
            return False, "Не удалось найти ID полей для логина и пароля"

        if debug:
            print(f"ID поля логина: {login_id}")
            print(f"ID поля пароля: {password_id}")
            print(f"ID чекбокса 'Запомнить меня': {remember_id}")

        # Поиск blazorSessionId в JavaScript
        scripts = soup.find_all("script")
        blazor_session_id = None

        # Ищем в исходном HTML
        match = re.search(
            r'blazorSessionId\s*[=:]\s*["\']([^"\']+)["\']', login_page_response.text
        )
        if match:
            blazor_session_id = match.group(1)
            if debug:
                print(f"Найден blazorSessionId в HTML: {blazor_session_id}")

        # Если не нашли, ищем в скриптах
        if not blazor_session_id:
            for script in scripts:
                if script.string and "blazorSessionId" in str(script.string):
                    match = re.search(
                        r'blazorSessionId\s*[=:]\s*["\']([^"\']+)["\']',
                        str(script.string),
                    )
                    if match:
                        blazor_session_id = match.group(1)
                        if debug:
                            print(
                                f"Найден blazorSessionId в скрипте: {blazor_session_id}"
                            )
                        break

        # Шаг 4: Извлечение securityHash
        security_hash = None
        security_hash2 = None

        # Ищем хеши безопасности в скриптах
        for script in scripts:
            if script.string:
                script_content = str(script.string)

                if "securityHash" in script_content:
                    hash_match = re.search(
                        r'securityHash\s*[=:]\s*["\']([^"\']+)["\']', script_content
                    )
                    if hash_match:
                        security_hash = hash_match.group(1)

                if "securityHash2" in script_content:
                    hash2_match = re.search(
                        r'securityHash2\s*[=:]\s*["\']([^"\']+)["\']', script_content
                    )
                    if hash2_match:
                        security_hash2 = hash2_match.group(1)

        # Если не нашли в скриптах, ищем в HTML
        if not security_hash:
            hash_match = re.search(
                r'securityHash\s*[=:]\s*["\']([^"\']+)["\']', login_page_response.text
            )
            if hash_match:
                security_hash = hash_match.group(1)

        if not security_hash2:
            hash2_match = re.search(
                r'securityHash2\s*[=:]\s*["\']([^"\']+)["\']', login_page_response.text
            )
            if hash2_match:
                security_hash2 = hash2_match.group(1)

        if debug:
            print(f"securityHash: {security_hash}")
            print(f"securityHash2: {security_hash2}")

        # Шаг 5: Подготовка запроса на авторизацию
        login_url = "https://www.ziva-fitness.com/login/"

        # Хеши для методов установки имени пользователя и пароля
        # Эти хеши обычно фиксированные и могут быть извлечены из оригинального JSON запроса
        username_method_hash = "Zb3XfwHeNHDbnBx5RMzhIfaMbSsCYf56vtSPbUIpKfI="
        password_method_hash = "l2ndA47ONhlqd0+fcwpTiZYJ8SS1GZbUDDDQZGUy5Sg="
        remember_method_hash = "PzFF8otcughRuHG0K+IoeC00bLw26Ot6NF3rnyFJiE0="

        # Создаем payload
        payload = {
            "data": {
                "ownerViewName": "Login2",
                "ownerViewClassName": "LoginView v1b v1 bs-view dcon dc482 Login2",
                "action": "Login",
                "propertyValues": [
                    {
                        "dataName": "Login",
                        "dataType": "Base.Mvc.Models.ILoginModel, Base.Mvc, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null",
                        "methodSignature": "set_UserName-S",
                        "securityHash": username_method_hash,
                        "values": [{"Value": username}],
                        "originalValues": [{"Value": ""}],
                    },
                    {
                        "dataName": "Login",
                        "dataType": "Base.Mvc.Models.ILoginModel, Base.Mvc, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null",
                        "methodSignature": "set_Password-S",
                        "securityHash": password_method_hash,
                        "values": [{"Value": password}],
                        "originalValues": [{"Value": ""}],
                    },
                    {
                        "dataName": "Login",
                        "dataType": "Base.Mvc.Models.ILoginModel, Base.Mvc, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null",
                        "methodSignature": "set_PermanentLogin-B",
                        "securityHash": remember_method_hash,
                        "values": [{"Value": True}],
                        "originalValues": [{"Value": False}],
                    },
                ],
                "args": [],
                "securityHash": (
                    security_hash
                    if security_hash
                    else "sRy1oCsGVZy1hJdNzIFW+rVIrZZLvppLFMWa3qoH1h4="
                ),
                "securityHash2": (
                    security_hash2
                    if security_hash2
                    else "Avy3YHtH8PNDq7dlk0p5HreI7v5Ds34zHpgzFlImIEU="
                ),
            }
        }

        # Добавляем blazorSessionId, если нашли
        if blazor_session_id:
            payload["data"]["blazorSessionId"] = blazor_session_id
        else:
            # Если не нашли, используем ID из оригинального запроса
            payload["data"]["blazorSessionId"] = "59c82aae-32ff-462d-9d16-8f2bbb74db77"

        # Заголовки для запроса авторизации
        auth_headers = {
            "accept": "*/*",
            "content-type": "application/json; charset=UTF-8",
            "origin": "https://www.ziva-fitness.com",
            "referer": "https://www.ziva-fitness.com/login/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
            "sec-ch-ua": '"Not-A.Brand";v="99", "Chromium";v="124"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }

        # Шаг 6: Отправляем запрос на авторизацию
        print("Шаг 6: Отправка запроса авторизации...")
        auth_response = session.post(login_url, headers=auth_headers, json=payload)

        if debug:
            print(f"Статус ответа авторизации: {auth_response.status_code}")
            print(f"Текст ответа: {auth_response.text[:200]}...")
            print(f"Куки после авторизации: {session.cookies.get_dict()}")

        if auth_response.status_code != 200:
            return (
                False,
                f"Ошибка при авторизации. Код ответа: {auth_response.status_code}",
            )

        # Проверяем, есть ли ошибки в ответе
        if "error" in auth_response.text.lower():
            return False, f"Ошибка при авторизации: {auth_response.text}"

        # Шаг 7: Проверяем, что авторизация прошла успешно
        print("Шаг 7: Проверка успешности авторизации...")
        check_auth = session.get(
            "https://www.ziva-fitness.com/account/", headers=headers
        )

        if "/login/" in check_auth.url:
            return False, "Авторизация не удалась. Перенаправлено на страницу логина."

        if debug:
            print(f"Статус проверки авторизации: {check_auth.status_code}")
            print(f"URL после проверки: {check_auth.url}")

        # Шаг 8: Загружаем целевую страницу
        print(f"Шаг 8: Загрузка целевой страницы: {target_url}")
        target_response = session.get(target_url, headers=headers)

        if target_response.status_code != 200:
            return (
                False,
                f"Не удалось загрузить целевую страницу. Код ответа: {target_response.status_code}",
            )

        if "/login/" in target_response.url:
            return (
                False,
                "Перенаправлено на страницу логина при загрузке целевой страницы.",
            )

        if debug:
            print(f"Статус загрузки целевой страницы: {target_response.status_code}")
            print(f"URL целевой страницы: {target_response.url}")

        # Генерируем имя выходного файла, если не указано
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            product_id = (
                target_url.split("/?")[0].split("-p")[-1]
                if "-p" in target_url
                else "page"
            )
            output_file = f"ziva_product_{product_id}_{timestamp}.html"

        # Сохраняем HTML-страницу
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(target_response.text)

        print(f"HTML-страница сохранена в файл: {output_file}")

        return True, output_file

    except Exception as e:
        return False, f"Произошла ошибка: {str(e)}"


if __name__ == "__main__":
    # Параметры
    USERNAME = "hdsport2006@gmail.com"
    PASSWORD = "03CkAfC2"
    TARGET_URL = "https://www.ziva-fitness.com/xp-barbell-rack-p39184/?cid=19"

    # Выполняем вход и сохраняем страницу
    success, result = login_and_save_page(USERNAME, PASSWORD, TARGET_URL, debug=True)

    if success:
        print(f"Страница успешно сохранена в файл: {result}")
    else:
        print(f"Ошибка: {result}")
