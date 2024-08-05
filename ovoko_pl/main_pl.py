import asyncio
import json
import os
from datetime import datetime
import aiofiles
from playwright.async_api import async_playwright
import asyncio
import time
import os

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
all_hotels = os.path.join(temp_path, "all_hotels")
hotel_path = os.path.join(temp_path, "hotel")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(all_hotels, exist_ok=True)
os.makedirs(hotel_path, exist_ok=True)


async def save_response_json(json_response, url_name):
    """Асинхронно сохраняет JSON-данные в файл."""
    filename = os.path.join(hotel_path, f"{url_name}.json")
    async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(json_response, ensure_ascii=False, indent=4))


async def log_response(response, url_name):
    api_url = "https://www.kupujemprodajem.com/api/web/v1/search"
    request = response.request
    if request.method == "GET" and api_url in request.url:
        try:
            json_response = await response.json()
            await save_response_json(json_response, url_name)
        except Exception as e:
            print(f"Ошибка при получении JSON из ответа {response.url}: {e}")


async def main():
    async with async_playwright() as playwright:

        for i in range(10, 100):
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context()

            # Установим заголовки
            await context.set_extra_http_headers(
                {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "application/json",
                }
            )

            page = await context.new_page()

            page.on(
                "response",
                lambda response: asyncio.create_task(log_response(response, url_name)),
            )
            url_name = f"page_0{i}"
            url = f"https://www.kupujemprodajem.com/namestaj/stolovi-i-stolice/grupa/1268/395/2?page={i}"
            await page.goto(url)
            # Ждём появления кнопки "Принять все" и кликаем по ней, если она существует
            try:
                # Ожидание появления элемента
                await page.wait_for_selector(
                    "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
                    timeout=10000,
                )
                # Клик по элементу
                await page.click(
                    "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"
                )
                print("Кнопка 'Принять все' найдена и нажата.")
            except Exception as e:
                print("Кнопка 'Принять все' не найдена или не появилась вовремя.")
            await asyncio.sleep(5)
            # Ждём, пока элемент пагинации станет видимым, и кликаем по нему
            await page.wait_for_selector(
                "#search > section.content > div.pagination.pagination--bottom > div.pagination__pages > ul > li:nth-child(5)",
                timeout=10000,
            )
            await page.click(
                "#search > section.content > div.pagination.pagination--bottom > div.pagination__pages > ul > li:nth-child(5)"
            )

            # Добавьте необходимое время для просмотра результата
            await browser.close()


print("Вставьте ссылку")

asyncio.run(main())
