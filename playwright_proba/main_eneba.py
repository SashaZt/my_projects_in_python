import asyncio
import json
import random
from pathlib import Path

from logger import logger
from playwright.async_api import async_playwright

# Пути и директории
current_directory = Path.cwd()
json_directory = current_directory / "json"
html_directory = current_directory / "html"
json_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://www.eneba.com/"


async def run(playwright, urls):
    # Запускаем браузер
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        bypass_csp=True,
        java_script_enabled=True,
        permissions=["geolocation"],
        device_scale_factor=1.0,
        has_touch=True,
        ignore_https_errors=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    )
    page = await context.new_page()

    # Функция для перехвата запросов
    async def handle_request(request):
        if request.url == "https://www.eneba.com/graphql/" and request.method == "POST":
            try:
                post_data = request.post_data
                if post_data:
                    payload = json.loads(post_data)
                    operation_name = payload.get("operationName")
                    if (
                        operation_name == "WickedNoCache"
                    ):  # Оставляем только WickedNoCache
                        request_data = {
                            "url": request.url,
                            "method": request.method,
                            "operationName": operation_name,
                            "payload": payload,
                        }
                        request._captured_data = request_data
            except Exception as e:
                logger.error(f"Ошибка при обработке запроса: {e}")

    # Функция для перехвата ответов
    async def handle_response(response):
        if (
            response.url == "https://www.eneba.com/graphql/"
            and response.request.method == "POST"
        ):
            try:
                request_data = getattr(response.request, "_captured_data", None)
                if request_data and request_data["operationName"] == "WickedNoCache":
                    response_json = await response.json()
                    captured_data.append(
                        {"request": request_data, "response": response_json}
                    )
                    captured_operations.add(request_data["operationName"])
                    logger.info(
                        f"Перехвачен ответ для: {request_data['operationName']}"
                    )
            except Exception as e:
                logger.error(f"Ошибка при обработке ответа: {e}")

    # Подключаем обработчики
    page.on("request", handle_request)
    page.on("response", handle_response)

    # Обрабатываем каждый URL
    for product_slug_str in urls:
        # Формируем имена файлов
        price_file = json_directory / f"{product_slug_str.replace('/', '_')}_price.json"
        html_file = html_directory / f"{product_slug_str.replace('/', '_')}.html"

        # Проверяем, существуют ли оба файла
        if price_file.exists() and html_file.exists():
            logger.info(f"Файлы для {product_slug_str} уже существуют, пропускаем")
            continue

        # Очищаем данные перед обработкой новой страницы
        captured_data = []
        captured_operations = set()

        # Переходим на страницу
        logger.info(f"Переход на страницу: {BASE_URL}{product_slug_str}")
        await page.goto(f"{BASE_URL}{product_slug_str}")

        # Ждём, пока не получим ответ WickedNoCache
        timeout = 30
        start_time = asyncio.get_event_loop().time()
        while "WickedNoCache" not in captured_operations:  # Ждём только один ответ
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.warning(
                    f"Таймаут для {product_slug_str}: не удалось собрать ответ WickedNoCache"
                )
                break
            await asyncio.sleep(1)

        # Сохраняем данные в JSON-файл, если есть
        if captured_data:
            with open(price_file, "w", encoding="utf-8") as f:
                json.dump(captured_data, f, ensure_ascii=False, indent=4)
            logger.info(
                f"Сохранено {len(captured_data)} пар запрос-ответ в {price_file}"
            )
        else:
            logger.warning(f"Нет данных для сохранения в {price_file}")

        # Сохраняем HTML страницы
        html_content = await page.content()
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"HTML сохранён в {html_file}")

        # Случайная задержка
        number = random.uniform(5, 10)
        await asyncio.sleep(number)

    # Закрываем браузер
    await browser.close()


async def main(urls):
    async with async_playwright() as playwright:
        await run(playwright, urls)


def get_skug():
    with open("bd.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    skugs = []
    for item in data:
        product_slug = item.get("product_slug")
        if product_slug:
            skugs.append(product_slug)
    return skugs


if __name__ == "__main__":
    skugs = get_skug()
    asyncio.run(main(skugs))
