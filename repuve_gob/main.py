import asyncio
import json
import os
from datetime import datetime
import aiofiles
from playwright.async_api import async_playwright
import time

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
all_hotels = os.path.join(temp_path, "all_hotels")
hotel_path = os.path.join(temp_path, "hotel")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(all_hotels, exist_ok=True)
os.makedirs(hotel_path, exist_ok=True)


async def save_response_json(json_response, number):
    """Асинхронно сохраняет JSON-данные в файл."""
    filename = os.path.join(hotel_path, f"{number}.json")
    async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(json_response, ensure_ascii=False, indent=4))


async def main(url):
    timeout_selector = 60000
    async with async_playwright() as playwright:
        proxy_host = "proxy.scrapingant.com"
        proxy_port = 443
        proxy_user = "scrapingant"
        proxy_pass = "5762b6b89e9e4462baf572e921fade22"
        proxy = {
            "server": f"http://{proxy_host}:{proxy_port}",
            "username": proxy_user,
            "password": proxy_pass,
        }
        browser = await playwright.chromium.launch(headless=False, proxy=proxy)
        context = await browser.new_context()
        page = await context.new_page()

        # Устанавливаем обработчик для сбора и сохранения данных ответов
        def create_log_response_with_counter(number):
            async def log_response(response):
                api_url = "https://www2.repuve.gob.mx:8443/consulta/consulta/repuve"
                request = response.request
                if request.method == "POST" and api_url in request.url:
                    try:
                        json_response = await response.json()
                        await save_response_json(json_response, number)
                    except Exception as e:
                        print(
                            f"Ошибка при получении JSON из ответа {response.url}: {e}"
                        )

            return log_response

        numbers = [
            "NGU8989",
            "NCV2895",
            "MMT832A",
            "MNW954A",
            "C53AVJ",
            "53f878",
            "773YMZ",
            "247VDK",
            "XZE363B",
            "YEC678B",
        ]
        response_handlers = {}

        for number in numbers:

            await page.goto(url, wait_until="networkidle", timeout=timeout_selector)
            button_selector = "//button[h6[text()='ENTENDIDO']]"

            button = await page.wait_for_selector(
                button_selector, timeout=timeout_selector
            )
            await button.click()  # Кликаем по кнопке
            input_selector = "input[placeholder='AA123D']"
            await page.fill(input_selector, number)  # Заполняем input значением number

            # Находим кнопку с текстом "Buscar" и кликаем по ней
            button_selector = "//button[contains(text(), 'Buscar')]"
            buscar_button = await page.wait_for_selector(button_selector)
            await buscar_button.click()  # Кликаем по кнопке

            handler = create_log_response_with_counter(number)
            response_handlers[number] = handler
            page.on("response", handler)

            await asyncio.sleep(5)

            # Удаляем обработчик и очищаем инпут
            page.remove_listener("response", response_handlers[number])
            # await page.evaluate(
            #     """() => {
            #     document.querySelector("input[placeholder='AA123D']").value = '';
            # }"""
            # )

            # Удаляем обработчик после первой итерации
            # if count > 1:
            #     page.remove_listener("response", response_handlers[numbers[count - 1]])
            # elif count > 1:
            #     page.remove_listener("response", response_handlers[numbers[count - 1]])

        # await asyncio.sleep(5)
        # # Здесь нажимаем кнопку cookies
        # button_cookies = '//button[@class="r-button r-button--accent r-button--hover r-button--contained r-button--only-text r-button--svg-margin-left r-consent-buttons__button cmpboxbtnyes"]'
        # await page.wait_for_selector(button_cookies, timeout=timeout_selector)
        # cookies_button = await page.query_selector(button_cookies)
        # if cookies_button:
        #     # Кликаем по кнопке "Следующая", если она найдена
        #     await cookies_button.click()

        # # Дождитесь загрузки страницы и элементов
        # await page.wait_for_selector(
        #     '//button[@class="r-select-button r-select-button-termin"]',
        #     timeout=timeout_selector,
        # )
        # termin_element = '//button[@class="r-select-button r-select-button-termin"]'
        # # Найдите все элементы по селектору
        # await page.wait_for_selector(termin_element, timeout=timeout_selector)
        # element_termin = await page.query_selector(termin_element)
        # # Проверка наличия элементов перед извлечением текста
        # # await asyncio.sleep(5)
        # if element_termin:
        #     await element_termin.click()
        # else:
        #     print("Элементы не найдены")
        # list_element = '//button[@class="r-tab"]'
        # # Найдите все элементы по селектору
        # await page.wait_for_selector(list_element, timeout=timeout_selector)
        # element_list = await page.query_selector(list_element)
        # # Проверка наличия элементов перед извлечением текста
        # # await asyncio.sleep(5)
        # if element_list:
        #     await element_list.click()
        # else:
        #     print("Элементы не найдены")
        # try:
        #     list_item = '//div[@class="kh-terminy-list__item"]'
        # except:
        #     list_item = (
        #         '//div[@class="kh-terminy-list__item kh-terminy-list__item--active"]'
        #     )
        # await page.wait_for_selector(list_item, timeout=timeout_selector)
        # item_list = await page.query_selector_all(list_item)
        # # Проверка наличия элементов перед извлечением текста
        # # await asyncio.sleep(5)
        # if item_list:
        #     await item_list[0].click()
        # else:
        #     print("Элементы не найдены")

        # Итерация по страницам

        await browser.close()


url = "https://www2.repuve.gob.mx:8443/ciudadania/"
asyncio.run(main(url))
