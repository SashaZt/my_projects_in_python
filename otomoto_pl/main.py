import asyncio
from playwright.async_api import async_playwright
import aiofiles
import time
import sys
import os
import json

current_directory = os.getcwd()


def load_config_headers():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "config.json")
    if not os.path.exists(filename_config):
        print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
        time.sleep(3)
        sys.exit(1)
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)

    return config


async def main(url, pages):
    config = load_config_headers()
    proxy_config = config.get("proxy")
    timeout = 3000
    all_datas = []

    browsers_path = os.path.join(current_directory, "pw-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False,
            proxy=proxy_config,
        )
        context = await browser.new_context()

        page = await context.new_page()

        # Блокировка загрузки изображений, стилей и других ресурсов
        async def block_resource(route, request):
            if request.resource_type in ["image", "stylesheet", "font", "media"]:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_resource)
        for ur in range(1, pages + 1):
            if ur == 1:
                await page.goto(url)
            else:
                await page.goto(f"{url}&page={ur}")

            # Обработка кнопки "Akceptuję"
            try:
                await page.wait_for_selector(
                    'button:has-text("Akceptuję")', timeout=timeout
                )
                await page.click('button:has-text("Akceptuję")')
            except:
                pass

            try:
                await asyncio.sleep(2)  # Даем время для загрузки всех элементов

                # Найти все article с data-orientation="horizontal"
                articles = await page.query_selector_all(
                    'article[data-orientation="horizontal"]'
                )

                for article in articles:
                    id_value = await article.get_attribute("data-id")
                    link = await article.query_selector('a:has-text("ad link")')

                    if link:
                        url_value = await link.get_attribute("href")
                        url_value = url_value.replace(".html", "")
                        all_datas.append({"id": id_value, "url": url_value})

            except Exception as e:
                print(f"Произошла ошибка при извлечении данных на странице {ur}: {e}")

        await browser.close()

        # Записываем данные в файл JSON
        async with aiofiles.open("links.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(all_datas, ensure_ascii=False, indent=4))


async def read_json(file_path):
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            contents = await f.read()
            data = json.loads(contents)
        return data
    except FileNotFoundError:
        return []


# Функция для удаления записей с tel_ad: null из data.json
async def clean_data_json():
    data = await read_json("data.json")
    cleaned_data = [entry for entry in data if entry["tel_ad"] is not None]

    async with aiofiles.open("data.json", "w", encoding="utf-8") as f:
        await f.write(json.dumps(cleaned_data, ensure_ascii=False, indent=4))


# Новые ссылки которые еще не проходили
async def filter_links():
    await clean_data_json()  # Очистка data.json перед фильтрацией

    existing_data = await read_json("data.json")
    links = await read_json("links.json")

    existing_ids = {entry["id_ad"] for entry in existing_data}
    new_links = [entry for entry in links if entry["id"] not in existing_ids]

    return new_links


# Формирование ссылки и ид
async def append_to_json(file_path, data):
    existing_data = await read_json(file_path)
    existing_data.extend(data)
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(existing_data, ensure_ascii=False, indent=4))


async def get_ad():
    config = load_config_headers()
    proxy_config = config.get("proxy")
    timeout = 3000
    extracted_data = await filter_links()
    all_datas = []
    browsers_path = os.path.join(current_directory, "pw-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False,
            proxy=proxy_config,
        )
        context = await browser.new_context(
            ignore_https_errors=True  # Игнорируем ошибки HTTPS
        )
        page = await context.new_page()

        # Блокировка загрузки изображений, стилей и других ресурсов
        async def block_resource(route, request):
            if request.resource_type in ["image", "stylesheet", "font", "media"]:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_resource)
        # Замените URL на актуальный
        await page.goto("https://www.otomoto.pl/", timeout=60000)
        await asyncio.sleep(2)
        try:
            await page.wait_for_selector(
                'button:has-text("Akceptuję")', timeout=timeout
            )
            await page.click('button:has-text("Akceptuję")')
        except:
            pass

        for ex in extracted_data:  # уберите [:2] чтобы обработать все данные
            id_ad = ex["id"]
            url = ex["url"]
            # Обработка кнопки "Akceptuję"
            try:
                await page.wait_for_selector(
                    'button:has-text("Akceptuję")', timeout=timeout
                )
                await page.click('button:has-text("Akceptuję")')
            except:
                pass

            tel_ad = None
            try:
                await page.goto(url, timeout=60000)  # Замените URL на актуальный
            except Exception as e:
                print(f"Ошибка при переходе по URL {url}: {e}")
                continue  # Пропускаем URL, если произошла ошибка при переходе

            # Получаем номер телефона
            try:
                span_element = await page.query_selector(
                    'span:has-text("Wyświetl numer")'
                )
                if span_element:
                    await span_element.click()
                    await asyncio.sleep(5)

                seller_info = await page.wait_for_selector(
                    'div[data-testid="aside-seller-info"]', timeout=timeout
                )
                if seller_info:
                    a_tags = await seller_info.query_selector_all('a[href^="tel:"]')
                    tel_hrefs = [await a.get_attribute("href") for a in a_tags]
                    for href in tel_hrefs:
                        tel_ad = href.replace("tel:", "")
                else:
                    continue

            except Exception as e:
                print(f"Произошла ошибка при извлечении номера на URL {url}: {e}")
                continue  # Пропускаем URL, если произошла ошибка при извлечении номера

            datas = {"id_ad": id_ad, "tel_ad": tel_ad}
            all_datas.append(datas)

            # Записываем данные в файл JSON на каждой итерации
            await append_to_json("data.json", all_datas)
            all_datas.clear()  # Очистить all_datas для следующей итерации

        await browser.close()


while True:
    print(
        "Введите 1 для получения ввсех ссылок на объявления"
        "\nВведите 2 для получения номеров"
        "\nВведите 0 Закрытия программы"
    )
    try:
        user_input = int(input("Выберите действие: "))
    except ValueError:  # Если введенные данные нельзя преобразовать в число
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
        continue  # Пропускаем оставшуюся часть цикла и начинаем с новой итерации
    if user_input == 1:
        url = str(input("Вставьте ссылку: "))
        pages = int(input("Количество страниц которое обойти: "))
        asyncio.run(main(url, pages))
    elif user_input == 2:
        asyncio.run(get_ad())

    elif user_input == 0:
        print("Программа завершена.")
        time.sleep(2)
        sys.exit(1)

# if __name__ == "__main__":
#     # url = "https://www.otomoto.pl/osobowe?search%5Bfilter_float_price%3Afrom%5D=5000"
#     url = str(input("Вставьте ссылку: "))
#     pages = int(input("Количество страниц которое обойти: "))
#     # pages = 3
#     # url = "https://www.otomoto.pl/osobowe?search%5Bfilter_float_price%3Afrom%5D=5000&page=2"
#     asyncio.run(main(url, pages))
#     asyncio.run(get_ad())
