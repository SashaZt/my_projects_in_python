import asyncio
import json
import os
from datetime import datetime
import aiofiles
from playwright.async_api import async_playwright
import time

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
repuve_path = os.path.join(temp_path, "repuve")
pgj_path = os.path.join(temp_path, "pgj")
ocra_path = os.path.join(temp_path, "ocra")
carfax_path = os.path.join(temp_path, "carfax")
aviso_path = os.path.join(temp_path, "aviso")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(repuve_path, exist_ok=True)
os.makedirs(pgj_path, exist_ok=True)
os.makedirs(ocra_path, exist_ok=True)
os.makedirs(carfax_path, exist_ok=True)
os.makedirs(aviso_path, exist_ok=True)


# Универсальная функция для сохранения JSON
async def save_response_json(json_response, number, path):
    """Асинхронно сохраняет JSON-данные в файл."""
    filename = os.path.join(path, f"{number}.json")
    async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(json_response, ensure_ascii=False, indent=4))


# Универсальная функция для ожидания и клика по элементу
async def wait_and_click(page, selector, timeout=10000):
    button = await page.wait_for_selector(selector, timeout=timeout)
    if button:
        await button.click()
        await page.wait_for_timeout(1000)  # Задержка для наглядности (необязательно)


# Функция для обработки ответов
def create_response_handler(number):
    async def log_response(response):
        url_to_path = {
            "https://www2.repuve.gob.mx:8443/consulta/consulta/repuve": repuve_path,
            "https://www2.repuve.gob.mx:8443/consulta/consulta/pgj": pgj_path,
            "https://www2.repuve.gob.mx:8443/consulta/consulta/ocra": ocra_path,
            "https://www2.repuve.gob.mx:8443/consulta/consulta/carfax": carfax_path,
            "https://www2.repuve.gob.mx:8443/consulta/consulta/aviso": aviso_path,
        }

        if response.request.method == "POST" and response.url in url_to_path:
            try:
                json_response = await response.json()
                path = url_to_path[response.url]
                await save_response_json(json_response, number, path)
            except Exception as e:
                print(f"Ошибка при получении JSON из ответа {response.url}: {e}")

    return log_response


async def main(url):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    timeout_selector = 90000
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)  # , proxy=proxy
        context = await browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080},  # Настройка размеров экрана
            device_scale_factor=1,  # Плотность пикселей
            is_mobile=False,
            has_touch=False,
            java_script_enabled=True,
            timezone_id="America/New_York",  # Настройка часового пояса
            geolocation={
                "latitude": 40.7128,
                "longitude": -74.0060,
            },  # Настройка геолокации
            permissions=["geolocation"],  # Включение разрешений
            locale="en-US",  # Настройка локали
            color_scheme="light",  # Настройка цветовой схемы
        )
        page = await context.new_page()

        numbers = ["NUE2691", "NUE2691"]  # Список номеров
        for number in numbers:
            await page.goto(url, wait_until="networkidle", timeout=timeout_selector)
            await wait_and_click(
                page, "//button[h6[text()='ENTENDIDO']]", timeout_selector
            )
            # Заполняем input значением number
            await page.fill("input[placeholder='AA123D']", number)
            await wait_and_click(
                page, "//button[contains(text(), 'Buscar')]", timeout_selector
            )

            handler = create_response_handler(number)
            page.on("response", handler)
            try:
                # Клики по различным кнопкам
                await wait_and_click(
                    page,
                    "//li[a[@data-toggle='tab' and @routerlink='/consulta/pgj' and @href='/ciudadania/consulta/pgj' and text()='FGJ']]",
                    1000,
                )
                await asyncio.sleep(1)
                await wait_and_click(
                    page,
                    "//li[a[@data-toggle='tab' and @routerlink='/consulta/ocra' and @href='/ciudadania/consulta/ocra' and text()='OCRA']]",
                    1000,
                )
                await asyncio.sleep(1)
                await wait_and_click(
                    page,
                    "//li[a[@data-toggle='tab' and @routerlink='/consulta/carfax' and @href='/ciudadania/consulta/carfax' and text()='Robo USA/CAN']]",
                    1000,
                )
                await asyncio.sleep(1)
                await wait_and_click(
                    page,
                    "//li[a[@data-toggle='tab' and @routerlink='/consulta/aviso' and @href='/ciudadania/consulta/aviso' and text()='Avisos Ministeriales/Judiciales']]",
                    1000,
                )
                await asyncio.sleep(1)
            except:
                continue

            page.remove_listener("response", handler)

            # await asyncio.sleep(5)  # Пауза для проверки (можно убрать)


if __name__ == "__main__":
    url = "https://www2.repuve.gob.mx:8443/ciudadania/"
    asyncio.run(main(url))
