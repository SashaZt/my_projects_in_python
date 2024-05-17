import asyncio
import json
import aiofiles
from playwright.async_api import async_playwright
import time
import os
from datetime import datetime
from selectolax.parser import HTMLParser

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


async def save_page_content_html(page, file_path):

    content = await page.content()
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(content)


async def main(url):
    now = datetime.now()
    time_now = now.strftime("%H:%M:%S")
    print(time_now)
    timeout_selector = 60000
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Устанавливаем обработчик для сбора и сохранения данных ответов
        def create_log_response_with_counter(url_name):
            async def log_response(response):
                api_url = "https://r.pl/api/wyszukiwarka/wyszukaj-kalkulator"
                request = response.request
                if (
                    request.method == "POST" and api_url in request.url
                ):  # Подставьте актуальное условие URL
                    try:
                        json_response = await response.json()
                        await save_response_json(json_response, url_name)

                    except Exception as e:
                        print(
                            f"Ошибка при получении JSON из ответа {response.url}: {e}"
                        )

            return log_response

        url_name = url.split("/")[-1]
        # filename = f"{url_name}.html"
        filename = "url_name.html"
        file_path = os.path.join(current_directory, filename)
        # Для сохранения html файла
        # if not os.path.exists(file_path):
        await page.goto(url)  # , wait_until="networkidle", timeout=60000
        await asyncio.sleep(1)
        await save_page_content_html(page, file_path)
        # try:
        #     await page.wait_for_selector(
        #         "button#onetrust-accept-btn-handler", timeout=10000
        #     )
        #     accept_button = await page.query_selector(
        #         "button#onetrust-accept-btn-handler"
        #     )

        #     if accept_button:
        #         await accept_button.click()
        #         await asyncio.sleep(1)
        #         await save_page_content_html(page, file_path)
        #     else:
        #         print("Accept button not found")
        # except Exception as e:
        #     print(f"An error occurred: {e}")

        # Для сохранения json файла
        handler = create_log_response_with_counter(url_name)
        page.on("response", handler)
        await asyncio.sleep(1)
        await browser.close()
        now = datetime.now()
        time_now = now.strftime("%H:%M:%S")
        print(time_now)
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

    # # Итерация по страницам


def parsing_num():
    all_href = []
    filename = "url_name.html"
    with open(filename, encoding="utf-8") as file:
        src = file.read()
    parser = HTMLParser(src)
    numbuttons = parser.css('a[class="button button-outline button-small numbutton"]')
    for num in numbuttons:
        href = num.attributes.get("href")
        all_href.append(href)
    print(all_href)





if __name__ == "__main__":
    # parsing_num()
    url = "https://smstome.com/usa/phone/12622727616/sms/6816"
    asyncio.run(main(url))
