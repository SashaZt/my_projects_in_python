import asyncio
import json

import requests
from playwright.async_api import async_playwright


async def capture_and_save_login_request(
    url: str, username: str, password: str, output_file: str = "login_request.json"
):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Список для хранения POST-запросов
        post_requests = []

        # Перехват сетевых запросов
        async def handle_request(route, request):
            if request.method == "POST":
                # Сохраняем все POST-запросы для отладки, но фильтруем позже
                post_requests.append(
                    {
                        "url": request.url,
                        "headers": request.headers,
                        "payload": request.post_data_json or request.post_data or {},
                    }
                )
            await route.continue_()

        await page.route("**/*", handle_request)

        # Переходим на страницу логина
        await page.goto(url)

        # Заполняем поле логина
        await page.fill('//input[@name="login"]', username)

        # Заполняем поле пароля
        await page.fill('//input[@name="password"]', password)

        # Ставим галочку на чекбоксе
        await page.check('//input[@class="permanentLogin"]')

        # Нажимаем на кнопку отправки формы
        await page.click('//a[@class="button login xta_doLogin"]')
        await page.wait_for_timeout(10000)

        # Выводим перехваченные POST-запросы
        print(
            "Перехваченные POST-запросы:",
            json.dumps(post_requests, indent=4, ensure_ascii=False),
        )

        # Выбираем запрос на авторизацию
        request_data = next(
            (
                req
                for req in post_requests
                if "/login/" in req["url"] and "google-analytics" not in req["url"]
            ),
            {},
        )

        # Сохраняем данные запроса в JSON-файл
        if request_data:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(request_data, f, ensure_ascii=False, indent=4)
            print(f"POST-запрос сохранен в {output_file}:", request_data)
        else:
            print("POST-запрос на авторизацию не найден.")
            return {}

        await browser.close()
        return request_data


def perform_login_with_requests(request_data: dict, username: str, password: str):
    if not request_data:
        print("Нет данных запроса для отправки.")
        return None

    # Получаем свежие cookies
    session = requests.Session()
    session.get("https://www.ziva-fitness.com/login/")
    headers = request_data["headers"].copy()
    headers["cookie"] = "; ".join(f"{k}={v}" for k, v in session.cookies.items())

    # Подготавливаем тело запроса
    payload = request_data.get("payload", {})
    if isinstance(payload, str):
        payload = json.loads(payload) if payload else {}
    elif payload is None:
        payload = {}

    # Обновляем логин и пароль
    if "data" in payload and "propertyValues" in payload["data"]:
        payload["data"]["propertyValues"][0]["values"][0]["Value"] = username
        payload["data"]["propertyValues"][1]["values"][0]["Value"] = password
        payload["data"]["propertyValues"][2]["values"][0]["Value"] = True

    # Отправляем POST-запрос
    try:
        response = requests.post(url=request_data["url"], headers=headers, json=payload)
        return response
    except Exception as e:
        print(f"Ошибка при отправке запроса: {e}")
        return None


async def main():
    # Пример использования
    login_url = "https://www.ziva-fitness.com/login/"  # Страница логина
    username = "hdsport2006@gmail.com"  # Логин
    password = "03CkAfC2"  # Пароль
    output_file = "login_request.json"

    # Захватываем и сохраняем POST-запрос
    request_data = await capture_and_save_login_request(
        login_url, username, password, output_file
    )

    # Проверяем авторизацию
    response = perform_login_with_requests(request_data, username, password)
    if response:
        print("Статус ответа:", response.status_code)
        print("Содержимое ответа:", response.text)


if __name__ == "__main__":
    asyncio.run(main())
