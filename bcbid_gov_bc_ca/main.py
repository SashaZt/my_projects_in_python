import asyncio
import json
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from playwright.async_api import async_playwright

# Указываем пути к файлам и папкам
current_directory = Path.cwd()
html_directory = current_directory / "html"
html_unverified_bid_results = current_directory / "html_unverified_bid_results"
html_directory.mkdir(parents=True, exist_ok=True)
html_unverified_bid_results.mkdir(parents=True, exist_ok=True)
unverified_bid_results_output_urls = (
    current_directory / "unverified_bid_results_output_urls.csv"
)


def read_urls_from_csv(csv_file_path):
    """
    Читает CSV файл и возвращает список URL-адресов.

    :param csv_file_path: Путь к CSV файлу.
    :return: Список URL-адресов.
    """
    # Проверяем, существует ли файл
    if not csv_file_path.exists():
        raise FileNotFoundError(f"Файл {csv_file_path} не найден.")

    # Читаем CSV файл с помощью pandas
    df = pd.read_csv(csv_file_path)

    # Проверяем, есть ли колонка "url"
    if "url" not in df.columns:
        raise ValueError(f"В файле {csv_file_path} отсутствует колонка 'url'.")

    # Возвращаем список URL
    return df["url"].tolist()


def extract_id_from_url(url):
    """
    Извлекает числовой ID из URL.

    :param url: URL строка.
    :return: Извлеченный ID как строка.
    """
    # Разбиваем строку по символу "/"
    parts = url.split("/")
    # Последняя часть после слеша содержит ID
    return parts[-1] if parts[-1].isdigit() else None


async def run_unverified_bid_results(playwright):
    # Запускаем браузер
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        bypass_csp=True,
        java_script_enabled=True,
        permissions=["geolocation"],
        device_scale_factor=1.0,
        has_touch=True,
        ignore_https_errors=True,
    )
    page = await context.new_page()

    # Отключаем загрузку изображений, шрифтов и других медиафайлов
    await context.route(
        "**/*",
        lambda route, request: (
            route.abort()
            if request.resource_type in ["image", "media", "font", "stylesheet"]
            else route.continue_()
        ),
    )

    # Переходим на URL
    url = "https://bcbid.gov.bc.ca/page.aspx/en/rfp/unverified_bids_browse_public"
    await page.goto(url)

    # Ожидаем начальную загрузку
    await asyncio.sleep(1)
    while True:
        # # Находим контейнер ul с классом "pager buttons"
        pager_element = await page.locator(
            '//ul[@class="pager buttons"]'
        ).element_handle()
        if not pager_element:
            logger.error("Не удалось найти контейнер 'pager buttons'.")
            break

        # Находим текущую страницу внутри ul
        current_page_element = await pager_element.query_selector(
            '//li[@aria-current="page"]/button'
        )
        if not current_page_element:
            logger.error("Не удалось найти текущую страницу.")
            break
        # Извлекаем атрибут aria-label
        aria_label = await current_page_element.get_attribute("aria-label")
        if not aria_label:
            logger.error("Атрибут 'aria-label' отсутствует у текущей страницы.")
            break

        # Извлекаем номер страницы
        try:
            number_page = int(aria_label.split()[-1].strip())
            logger.info(f"Текущая страница: {number_page}")
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка извлечения номера страницы: {e}")
            break
        html_file = html_directory / f"page_content{number_page}.html"

        # Проверяем, существует ли файл
        if html_file.exists():
            logger.info(f"Файл {html_file} уже существует. Пропускаем сохранение.")
        else:
            # Сохраняем содержимое страницы в файл
            html_content = await page.content()
            with open(html_file, "w", encoding="utf-8") as file:
                file.write(html_content)
            logger.info(
                f"Содержимое страницы {number_page} сохранено в файл {html_file}"
            )

        # Находим кнопку "Next page" внутри ul
        next_button = await pager_element.query_selector(
            '//button[@aria-label="Next page"]'
        )
        if not next_button:
            logger.info("Кнопка 'Next page' не найдена. Конец.")
            break

        # Кликаем по кнопке "Next page" и ждем загрузки
        await next_button.click()
        await asyncio.sleep(2)  # Пауза для загрузки страницы

    # Закрываем браузер
    await browser.close()


async def run(playwright):
    urls = read_urls_from_csv(unverified_bid_results_output_urls)
    # Запускаем браузер
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        bypass_csp=True,
        java_script_enabled=True,
        permissions=["geolocation"],
        device_scale_factor=1.0,
        has_touch=True,
        ignore_https_errors=True,
    )
    page = await context.new_page()

    # Отключаем загрузку изображений, шрифтов и других медиафайлов
    await context.route(
        "**/*",
        lambda route, request: (
            route.abort()
            if request.resource_type in ["image", "media", "font", "stylesheet"]
            else route.continue_()
        ),
    )
    for url in urls:
        extracted_id = extract_id_from_url(url)
        html_file = html_directory / f"{extracted_id}.html"

        # Проверяем, существует ли файл
        if html_file.exists():
            logger.info(f"Файл {html_file} уже существует. Пропускаем сохранение.")
            continue
        # Переходим на URL
        await page.goto(url, wait_until="networkidle")

        # Ожидаем начальную загрузку
        # await asyncio.sleep(1)

        # Сохраняем содержимое страницы в файл
        html_content = await page.content()
        with open(html_file, "w", encoding="utf-8") as file:
            file.write(html_content)
        logger.info(f"сохранено файл {html_file}")

    # Закрываем браузер
    await browser.close()


async def run_contract_awards(playwright):
    # Запускаем браузер
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        bypass_csp=True,
        java_script_enabled=True,
        permissions=["geolocation"],
        device_scale_factor=1.0,
        has_touch=True,
        ignore_https_errors=True,
    )
    page = await context.new_page()

    # Отключаем загрузку изображений, шрифтов и других медиафайлов
    await context.route(
        "**/*",
        lambda route, request: (
            route.abort()
            if request.resource_type in ["image", "media", "font", "stylesheet"]
            else route.continue_()
        ),
    )

    # Переходим на URL
    url = "https://bcbid.gov.bc.ca/page.aspx/en/ctr/contract_browse_public"
    await page.goto(url)

    # Ожидаем начальную загрузку
    await asyncio.sleep(1)
    while True:
        # # Находим контейнер ul с классом "pager buttons"
        pager_element = await page.locator(
            '//ul[@class="pager buttons"]'
        ).element_handle()
        if not pager_element:
            logger.error("Не удалось найти контейнер 'pager buttons'.")
            break

        # Находим текущую страницу внутри ul
        current_page_element = await pager_element.query_selector(
            '//li[@aria-current="page"]/button'
        )
        if not current_page_element:
            logger.error("Не удалось найти текущую страницу.")
            break
        # Извлекаем атрибут aria-label
        aria_label = await current_page_element.get_attribute("aria-label")
        if not aria_label:
            logger.error("Атрибут 'aria-label' отсутствует у текущей страницы.")
            break

        # Извлекаем номер страницы
        try:
            number_page = int(aria_label.split()[-1].strip())
            logger.info(f"Текущая страница: {number_page}")
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка извлечения номера страницы: {e}")
            break
        html_file = html_directory / f"page_content{number_page}.html"

        # Проверяем, существует ли файл
        if html_file.exists():
            logger.info(f"Файл {html_file} уже существует. Пропускаем сохранение.")
        else:
            # Сохраняем содержимое страницы в файл
            html_content = await page.content()
            with open(html_file, "w", encoding="utf-8") as file:
                file.write(html_content)
            logger.info(
                f"Содержимое страницы {number_page} сохранено в файл {html_file}"
            )

        # Находим кнопку "Next page" внутри ul
        next_button = await pager_element.query_selector(
            '//button[@aria-label="Next page"]'
        )
        if not next_button:
            logger.info("Кнопка 'Next page' не найдена. Конец.")
            break

        # Кликаем по кнопке "Next page" и ждем загрузки
        await next_button.click()
        await asyncio.sleep(1)  # Пауза для загрузки страницы

    # Закрываем браузер
    await browser.close()


async def main():
    async with async_playwright() as playwright:
        await run(playwright)


def scrap_html_contract_awards():
    # Список для хранения всех извлечённых данных
    all_data = []

    # Перебираем HTML файлы в директории
    for html_file in html_directory.glob("*.html"):
        print(f"Обрабатываем файл: {html_file.name}")

        # Читаем содержимое файла
        with html_file.open(encoding="utf-8") as file:
            html_content = file.read()

        # Создаем объект BeautifulSoup
        soup = BeautifulSoup(html_content, "lxml")

        # Находим таблицу по ID
        table = soup.find("table", {"id": "body_x_grid_grd"})
        if not table:
            print(f"Таблица не найдена в файле: {html_file.name}")
            continue

        # Извлекаем заголовки столбцов (thead)
        headers = [th.get_text(strip=True) for th in table.find("thead").find_all("th")]

        # Извлекаем строки таблицы (tbody)
        rows = table.find("tbody").find_all("tr")
        for row in rows:
            # Извлекаем данные ячеек строки
            cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
            # Создаем словарь, сопоставляя заголовки с ячейками
            row_data = dict(zip(headers, cells))
            all_data.append(row_data)
    output_file = "output_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
        # Создаем DataFrame из списка словарей
    df = pd.DataFrame(all_data)

    # Записываем DataFrame в Excel
    output_file = "output_data.xlsx"
    df.to_excel(output_file, index=False, sheet_name="Data")


def scrap_html():
    # Домен для добавления к URL
    base_url = "https://bcbid.gov.bc.ca"
    # Множество для хранения уникальных URL
    unique_urls = set()

    # Перебираем HTML файлы в директории
    for html_file in html_unverified_bid_results.glob("*.html"):
        logger.info(f"Обрабатываем файл: {html_file.name}")

        # Читаем содержимое файла
        with html_file.open(encoding="utf-8") as file:
            html_content = file.read()

        # Создаем объект BeautifulSoup
        soup = BeautifulSoup(html_content, "lxml")

        # Ищем таблицу по классу
        table = soup.find("table", {"class": "ui very compact table iv-grid-view"})
        if not table:
            logger.error(f"Таблица не найдена в файле: {html_file.name}")
            continue

        # Ищем все ссылки в таблице
        for a_tag in table.find_all("a", href=True):
            # Добавляем полный URL с доменом
            full_url = base_url + a_tag["href"]
            unique_urls.add(full_url)

    # Преобразуем множество обратно в список словарей для DataFrame
    urls = [{"url": url} for url in unique_urls]

    # Создаем DataFrame из списка URL
    df = pd.DataFrame(urls)

    # Сохраняем DataFrame в CSV файл
    df.to_csv(unverified_bid_results_output_urls, index=False)
    logger.info(
        f"Уникальные URL-адреса успешно сохранены в файл {unverified_bid_results_output_urls}"
    )


if __name__ == "__main__":
    # Запуск основной функции
    asyncio.run(main())
    # scrap_html()
