import asyncio
from playwright.async_api import async_playwright
import aiofiles
import time
import sys
import os
import json
import pandas as pd

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


async def main(url, pages_start, pages_finish):
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
        for ur in range(pages_start, pages_finish + 1):
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


# Функция для ожидания элемента и клика по нему
async def wait_and_click(page, selector, timeout=3000, retries=3):
    for _ in range(retries):
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            await page.click(selector)
            return True
        except Exception as e:
            print(f"Ошибка при клике на элемент {selector}: {e}")
            await asyncio.sleep(2)
    return False


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
        await asyncio.sleep(1)
        try:
            await page.wait_for_selector(
                'button:has-text("Akceptuję")', timeout=timeout
            )
            await page.click('button:has-text("Akceptuję")')
        except:
            pass

        for ex in extracted_data:
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
            await asyncio.sleep(2)
            tel_ad = None
            # Находим элемент //div[@data-testid="aside-seller-info"]
            seller_info_div = await page.wait_for_selector(
                '//div[@data-testid="aside-seller-info"]', timeout=60000
            )

            # Сначала ищем элемент span с текстом "Wyświetl numer"
            wyświetl_numer_span = await seller_info_div.query_selector(
                '//span[contains(@class, "button-text-wrapper") and text()="Wyświetl numer"]'
            )

            if not wyświetl_numer_span:
                # Если не нашли, ищем элемент span с текстом "Wyświetl numery"
                wyświetl_numer_span = await seller_info_div.query_selector(
                    '//span[contains(@class, "button-text-wrapper") and text()="Wyświetl numery"]'
                )

            if wyświetl_numer_span:
                # Попробуем три раза найти и кликнуть по элементу
                for attempt in range(3):
                    try:
                        await wyświetl_numer_span.click()
                        await asyncio.sleep(2)

                        # Ищем все элементы a с href, который начинается на "tel:"
                        phone_links = await seller_info_div.query_selector_all(
                            'a[href^="tel:"]'
                        )
                        phone_numbers = [
                            await link.get_attribute("href") for link in phone_links
                        ]
                        tel_ad = [
                            number.replace("tel:", "") for number in phone_numbers
                        ]
                        tel_ad = ",".join(tel_ad)
                        break
                    except Exception as e:
                        # print(f"Попытка {attempt + 1} не удалась: {e}")
                        await asyncio.sleep(1)  # Пауза перед повторной попыткой
            else:
                print(
                    "Не удалось найти элемент 'Wyświetl numer' или 'Wyświetl numery'."
                )

            datas = {"id_ad": id_ad, "tel_ad": tel_ad}
            all_datas.append(datas)

            # Записываем данные в файл JSON на каждой итерации
            await append_to_json("data.json", all_datas)
            all_datas.clear()  # Очистить all_datas для следующей итерации

        await browser.close()


def get_xlsx():
    # Загрузка данных из файла data.json
    with open("data.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    # Функция для форматирования номера телефона
    def format_phone_number(phone_number):
        phone_number = phone_number.replace(" ", "").replace("-", "")
        if phone_number.startswith("+48"):
            phone_number = phone_number[3:]
        return "+48" + phone_number

    # Извлечение и форматирование номеров телефонов, пропуская записи с tel_ad равным null
    formatted_numbers = []
    for entry in data:
        if entry["tel_ad"] is not None:
            if isinstance(entry["tel_ad"], str):
                phone_numbers = entry["tel_ad"].split(
                    ","
                )  # Разделяем номера по запятой
            elif isinstance(entry["tel_ad"], list):
                phone_numbers = entry["tel_ad"]
            else:
                continue

            formatted_phone_numbers = [
                format_phone_number(phone_number.strip())
                for phone_number in phone_numbers
            ]
            formatted_numbers.append(
                ", ".join(formatted_phone_numbers)
            )  # Объединяем номера в одну строку

    # Создание DataFrame только с номерами телефонов
    df = pd.DataFrame(formatted_numbers, columns=["tel_ad"])

    # Сохранение в Excel
    output_file = "phone_numbers.xlsx"
    df.to_excel(output_file, index=False)


while True:
    print(
        "Введите 1 для получения ввсех ссылок на объявления"
        "\nВведите 2 для получения номеров"
        "\nВведите 3 получить список номеров"
        "\nВведите 0 Закрытия программы"
    )
    try:
        user_input = int(input("Выберите действие: "))
    except ValueError:  # Если введенные данные нельзя преобразовать в число
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
        continue  # Пропускаем оставшуюся часть цикла и начинаем с новой итерации
    if user_input == 1:
        url = str(input("Вставьте ссылку: "))
        pages_start = int(input("Первая страница: "))
        pages_finish = int(input("Последняя страница: "))
        asyncio.run(main(url, pages_start, pages_finish))
    elif user_input == 2:
        asyncio.run(get_ad())
    elif user_input == 3:
        get_xlsx()

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
