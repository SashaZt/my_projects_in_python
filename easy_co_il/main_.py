import asyncio
import csv
import json
import os
import random
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Папка с JSON-файлами
input_folder = "json"

# Файл для записи результатов
output_file = "urls.csv"
current_directory = Path.cwd()
html_directory = current_directory / "html_pages"
html_directory.mkdir(parents=True, exist_ok=True)


async def main():
    # Создаем папку json, если она не существует
    os.makedirs("json", exist_ok=True)

    # Запускаем Playwright
    async with async_playwright() as p:
        # Настраиваем браузерные параметры для скрытия автоматизации
        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--ignore-certificate-errors",
            "--disable-extensions",
            "--disable-infobars",
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ]

        # Создаем браузерный контекст с высоким уровнем скрытности
        browser = await p.chromium.launch(
            headless=False,  # Браузер виден
            args=browser_args,
            devtools=False,  # Не открывать DevTools
        )

        # Создаем контекст с дополнительными параметрами для скрытия автоматизации
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},  # Стандартное разрешение
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",  # Современный UA
            java_script_enabled=True,  # Оставляем JS включенным
            ignore_https_errors=True,
        )

        # Устанавливаем скрипт для перекрытия WebDriver флагов
        await context.add_init_script(
            """
        // Скрываем признаки автоматизации
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        
        // Переопределяем navigator.plugins (должен быть не пустым)
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                return [1, 2, 3, 4, 5];
            },
        });
        
        // Переопределяем window.chrome
        window.chrome = {
            runtime: {},
        };
        
        // Удаляем детекторы для Playwright/Puppeteer
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """
        )

        # Создаем страницу
        page = await context.new_page()

        # Включаем перехват сетевых запросов
        await page.route("**/*", lambda route: route.continue_())

        # Массив для хранения перехваченных запросов
        captured_requests = []

        # Обработчик ответов
        async def on_response(response):
            url = response.url
            if url.startswith("https://easy.co.il/n/jsons/bizlist"):
                print(f"Перехвачен ответ: {url}")

                # Находим соответствующий запрос
                matching_request = None
                for req in captured_requests:
                    if req["url"] == url:
                        matching_request = req
                        break

                timestamp = (
                    matching_request["timestamp"]
                    if matching_request
                    else datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                )

                try:
                    # Получаем тело ответа в формате JSON
                    response_body = await response.json()

                    # Сохраняем ответ
                    filename = f"json/bizlist_response_{timestamp}.json"
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(response_body, f, ensure_ascii=False, indent=2)
                    print(f"Сохранен ответ JSON в {filename}")
                except Exception as e:
                    print(f"Ошибка при обработке ответа для {url}: {e}")

        # Регистрируем обработчики
        # page.on("request", on_request)
        page.on("response", on_response)
        regions = [
            1,
            2,
            3,
            4,
            5,
            6,
            26889570,
            1955,
            933,
            789,
            1783,
            1676,
            1825,
            322,
            1424,
            773,
            303,
            709,
            1804,
            1046,
            460,
            1841,
            310,
            759,
            1142,
            187,
            497,
            689,
            444,
            540,
            1604,
            1085,
            849,
            1324,
            1829,
            1780,
            1750,
            1749,
            1823,
            1409,
            1667,
            883,
        ]
        for region in regions:
            # Переходим на страницу
            await page.goto(
                f"https://easy.co.il/search/%D7%97%D7%91%D7%A8%D7%94%20%D7%90%D7%97%D7%96%D7%A7%D7%AA%20%D7%91%D7%99%D7%AA?region={region}",
                wait_until="networkidle",
            )

            # Ждем, чтобы страница полностью загрузилась
            await asyncio.sleep(random.uniform(3, 7))

            while True:
                # Прокручиваем страницу до конца
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)  # Ждем загрузки контента

                # Ищем кнопку "עוד תוצאות"
                try:
                    # Пробуем найти кнопку
                    button = None
                    for _ in range(5):  # Пробуем 5 раз с интервалом 1 секунда
                        button = page.locator("button.next-page-button")
                        if await button.count() > 0:
                            break
                        await asyncio.sleep(1)

                    # Проверяем, нашли ли кнопку
                    if await button.count() == 0:
                        print("Кнопка 'עוד תוצאות' не найдена. Остановка.")
                        break

                    # Нажимаем на кнопку
                    await button.click()
                    print("Нажата кнопка 'עוד תוצאות'")
                    await asyncio.sleep(2)  # Ждем загрузки нового контента
                except Exception as e:
                    print(f"Ошибка при поиске или нажатии кнопки: {e}")
                    break

        # Закрываем браузер
        await browser.close()


def scrap_json(input_folder="json", output_file="urls.csv"):
    """
    Извлекает из JSON-файлов ID элементов и формирует URL-адреса.

    Args:
        input_folder: папка с JSON-файлами
        output_file: выходной CSV-файл с URL-адресами
    """
    # Создаем список для хранения URL
    all_urls = []

    # Проходим по всем файлам в папке
    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(input_folder, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Извлекаем список из bizlist["list"]
                    biz_list = data.get("bizlist", {}).get("list", [])

                    # Если нашли список бизнесов
                    if biz_list:
                        for item in biz_list:
                            id_value = item.get("id")
                            if id_value:
                                # Формируем корректный URL
                                url = f"https://easy.co.il/page/{id_value}"
                                all_urls.append(url)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Ошибка при обработке файла {file_path}: {e}")

    # Убираем дубликаты URL-адресов
    unique_urls = list(set(all_urls))

    # Создаем DataFrame и сохраняем в CSV
    df = pd.DataFrame(unique_urls, columns=["url"])
    df.to_csv(output_file, index=False)

    print(
        f"Извлечено {len(unique_urls)} уникальных URL. Результаты сохранены в {output_file}."
    )


async def save_html_pages(csv_file="urls.csv", output_folder="html_pages"):
    """
    Открывает URL-адреса из CSV-файла и сохраняет HTML-страницы.

    Args:
        csv_file: CSV-файл с URL-адресами
        output_folder: папка для сохранения HTML-файлов
    """
    # Создаем папку для HTML-файлов, если она не существует
    os.makedirs(output_folder, exist_ok=True)

    # Загружаем CSV с URL-адресами
    df = pd.read_csv(csv_file)
    urls = df["url"].tolist()

    print(f"Загружено {len(urls)} URL-адресов из {csv_file}")

    # Запускаем Playwright
    async with async_playwright() as p:
        # Настраиваем браузерные параметры для скрытия автоматизации
        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--ignore-certificate-errors",
            "--disable-extensions",
            "--disable-infobars",
        ]

        # Создаем браузер
        browser = await p.chromium.launch(
            headless=False,  # Браузер виден
            args=browser_args,
        )

        # Создаем контекст с дополнительными параметрами для скрытия автоматизации
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            java_script_enabled=True,
        )

        # Добавляем скрипт для маскировки автоматизации
        await context.add_init_script(
            """
        // Скрываем признаки автоматизации
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        
        // Переопределяем navigator.plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Переопределяем window.chrome
        window.chrome = {
            runtime: {},
        };
        
        // Удаляем детекторы для Playwright/Puppeteer
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """
        )

        # Создаем страницу
        page = await context.new_page()

        # Обрабатываем каждый URL
        for i, url in enumerate(urls):
            try:
                # Извлекаем ID из URL
                path_parts = urlparse(url).path.split("/")
                page_id = path_parts[-1]

                # Формируем имя файла
                file_name = f"{page_id}.html"
                file_path = os.path.join(output_folder, file_name)

                # Проверяем, существует ли файл
                if os.path.exists(file_path):
                    print(
                        f"Файл {file_name} уже существует, пропускаем ({i+1}/{len(urls)})"
                    )
                    continue

                # Переходим на страницу
                print(f"Открываем {url} ({i+1}/{len(urls)})")
                await page.goto(url, wait_until="networkidle")

                # Ждем 2 секунды
                await asyncio.sleep(2)

                # Получаем HTML-контент
                html_content = await page.content()

                # Сохраняем HTML-файл
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

                print(f"Сохранен HTML в {file_path}")

                # Добавляем небольшую случайную паузу между запросами
                await asyncio.sleep(
                    1 + (hash(url) % 3) * 0.5
                )  # Случайная пауза от 1 до 2.5 секунд

            except Exception as e:
                print(f"Ошибка при обработке {url}: {e}")

        # Закрываем браузер
        await browser.close()
        print("Сохранение HTML-страниц завершено.")


def save_pages_from_csv(csv_file="urls.csv", output_folder="html_pages"):
    asyncio.run(save_html_pages(csv_file, output_folder))


def extract_product_data(soup):
    result = {
        "website": None,
        "facebook": None,
        "instagram": None,
        "phones": [],
        "email": None,
        "zipcode": None,
        "name": None,
    }

    info_box = soup.find("ul", class_="info-box")
    if info_box:
        for li in info_box.find_all("li", class_="info-item"):
            item_id = li.get("id", "")
            label = li.find("span")
            if not label:
                continue
            value = label.get_text(strip=True)

            if item_id == "sidebarBtn_homepage":
                result["website"] = value
            elif item_id == "sidebarBtn_facebook":
                result["facebook"] = value
            elif item_id == "sidebarBtn_instagram":
                result["instagram"] = value
            elif item_id == "sidebarBtn_callphone":
                result["phones"].append(value)
            elif item_id == "sidebarBtn_message":
                result["email"] = value
            elif "מיקוד" in value or "zipcode" in value.lower():
                result["zipcode"] = value.replace("מיקוד:", "").strip()

    # Обрабатываем <script type="application/ld+json">
    script_tag = soup.find("script", type="application/ld+json")
    if script_tag:
        try:
            json_data = json.loads(script_tag.string)
            result["name"] = json_data.get("name")
        except json.JSONDecodeError:
            pass

    # Преобразуем телефоны в строку через запятую
    if result["phones"]:
        result["phones"] = ", ".join(result["phones"])
    else:
        result["phones"] = None

    return result


def parse_info_box():
    # Создаем объект BeautifulSoup для парсинга HTML
    # logger.info(f"Обрабатываем директорию: {html_directory}")
    all_data = []

    # Проверяем наличие HTML-файлов
    html_files = list(html_directory.glob("*.html"))

    # Обрабатываем каждый HTML-файл
    for html_file in html_files:
        with html_file.open(encoding="utf-8") as file:
            content = file.read()
        soup = BeautifulSoup(content, "lxml")
        result = extract_product_data(soup)
        if result:
            # logger.info(json.dumps(result, ensure_ascii=False, indent=4))
            all_data.append(result)

    with open("output_json_file.json", "w", encoding="utf-8") as json_file:
        json.dump(all_data, json_file, ensure_ascii=False, indent=4)
    # Создание DataFrame и запись в Excel
    df = pd.DataFrame(all_data)
    df.to_excel("feepyf.xlsx", index=False)
    # return result


# Запускаем основную функцию
if __name__ == "__main__":
    # asyncio.run(main())
    # scrap_json()
    save_pages_from_csv()
    parse_info_box()
