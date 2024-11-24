import asyncio
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
from configuration.logger_setup import logger
from playwright.async_api import async_playwright

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)

output_csv_file = data_directory / "output.csv"


def read_from_csv(input_csv_file):
    # Загрузка CSV-файла с указанием, что столбец "url" является строкой
    df = pd.read_csv(input_csv_file, dtype={"url": str})
    return df["url"].tolist()


async def random_pause():
    pause_time = (
        random.randint(10, 30) * 1000
    )  # Случайная пауза от 5 до 10 секунд в миллисекундах
    await asyncio.sleep(pause_time / 1000)


async def search_inn(inns):
    # protocol = "http"
    # server = "res.proxy-seller.io:10000"
    # username = "57e9132c4de5b24e"
    # password = "RNW78Fm5"
    # proxy_config = {
    #     "server": f"{protocol}://{server}",
    #     "username": username,
    #     "password": password,
    # }
    # proxy_config = {
    #     "server": "http://37.48.118.4:13010",
    # }
    proxy_config = {}
    async with async_playwright() as p:
        # browser = await p.chromium.launch(proxy=proxy_config, headless=False)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        for inn in inns:
            try:
                file_path = html_files_directory / f"{inn}.html"
                if file_path.exists():
                    continue

                # Открытие URL
                await page.goto("https://www.osoo.kg/", wait_until="domcontentloaded")
                await random_pause()  # Пауза после загрузки URL

                # Вставка ИНН в поле ввода и нажатие кнопки поиска
                await page.fill("input#id_text", inn)
                await random_pause()  # Пауза после заполнения поля
                await page.click("button#button-search")
                await page.wait_for_load_state(
                    "domcontentloaded"
                )  # Ожидание полной загрузки страницы
                await random_pause()  # Пауза для загрузки страницы

                # Поиск элемента таблицы и проверка совпадения ИНН
                row = await page.wait_for_selector(
                    "table.table.table-striped tbody tr", timeout=10000
                )  # Ожидание появления таблицы
                if row:
                    await random_pause()  # Случайная пауза после клика по ссылке
                    inn_element = await row.query_selector("a[href^='/inn/']")
                    if inn_element:
                        retrieved_inn = await inn_element.inner_text()
                        if retrieved_inn == inn:
                            # Переход по ссылке
                            await inn_element.click()
                            await page.wait_for_load_state(
                                "domcontentloaded"
                            )  # Ожидание полной загрузки после перехода
                            await random_pause()  # Случайная пауза после клика по ссылке  # Пауза после клика по ссылке

                            # Ожидание появления элемента с информацией об организации
                            await page.wait_for_selector(
                                "#company-title", timeout=10000
                            )
                            await random_pause()  # Случайная пауза после клика по ссылке

                            # Получение контента страницы и сохранение в HTML-файл
                            content = await page.content()
                            with open(file_path, "w", encoding="utf-8") as file:
                                file.write(content)
                            logger.info(file_path)
            except Exception as e:
                print(f"Ошибка при обработке ИНН {inn}: {e}")

        # Закрытие браузера
        await browser.close()


async def main():
    urls = read_from_csv(output_csv_file)
    n = 5  # Количество потоков
    chunk_size = len(urls) // n
    tasks = []

    # Разделение списка URL на чанки и запуск асинхронных задач в потоках
    for i in range(n):
        start_index = i * chunk_size
        end_index = None if i == n - 1 else (i + 1) * chunk_size
        chunk = urls[start_index:end_index]
        tasks.append(search_inn(chunk))

    await asyncio.gather(*tasks)


# Запуск основных задач
asyncio.run(main())
