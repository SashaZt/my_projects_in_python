import asyncio
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from playwright.async_api import async_playwright
import pandas as pd
from tqdm import tqdm
from configuration.logger_setup import logger
import xml.etree.ElementTree as ET
import re
import aiofiles
import json
import os
import requests

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
pdf_files_directory = current_directory / "pdf_files"
json_responses_directory = current_directory / "json_responses"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
pdf_files_directory.mkdir(exist_ok=True, parents=True)

output_csv_file = data_directory / "output.csv"
file_json = json_responses_directory / "post_response.json"
csv_file_successful = data_directory / "successful.csv"

# Проверка и создание файла успешных URL
if not csv_file_successful.exists():
    pd.DataFrame(columns=["url"]).to_csv(csv_file_successful, index=False)


# Функция для получения списка URL
def get_urls(file_path):
    df = pd.read_csv(file_path)
    return df.iloc[:, 0].dropna().tolist()


# Функция загрузки списка прокси
def load_proxies():
    file_path = "roman.txt"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in file]
        logger.info(f"Загружено {len(proxies)} прокси.")
        return proxies
    else:
        logger.warning(
            "Файл с прокси не найден. Работа будет выполнена локально без прокси."
        )
        return []


# Асинхронная функция для сохранения HTML и получения ссылок по XPath
async def single_html(urls):
    proxies = load_proxies()
    proxy = random.choice(proxies) if proxies else None
    if not proxies:
        logger.info("Прокси не найдено, работа будет выполнена локально.")

    # Чтение успешных URL из файла
    successful_urls = set(pd.read_csv(csv_file_successful)["url"].tolist())

    try:
        proxy_config = parse_proxy(proxy) if proxy else None
        async with async_playwright() as p:
            browser = (
                await p.chromium.launch(proxy=proxy_config, headless=False)
                if proxy
                else await p.chromium.launch(headless=False)
            )
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()

            # Отключаем медиа
            await page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type in ["image", "media"]
                    else route.continue_()
                ),
            )
            for url in urls:
                if url in successful_urls:
                    logger.info(f"URL {url} уже обработан, пропуск итерации.")
                    continue

                # Переход на страницу и ожидание полной загрузки
                await page.goto(url, timeout=60000, wait_until="networkidle")

                # Извлечение data-aeat-id из элемента h2
                try:
                    h2_element = await page.wait_for_selector(
                        "h2.h4.mb-3[data-aeat-id]", timeout=5000
                    )
                    data_aeat_id = await h2_element.get_attribute("data-aeat-id")
                    logger.info(data_aeat_id)
                    if not data_aeat_id:
                        logger.warning(
                            f"data-aeat-id не найден на странице {url}. Пропуск итерации."
                        )
                        continue
                except:
                    continue

                # Скачивание PDF через Playwright
                # Скачивание PDF через Playwright, используя POST запрос
                try:
                    response = await page.evaluate(
                        "async (idRCRD) => {"
                        "  const formData = new FormData();"
                        "  formData.append('operacion', 'GET');"
                        "  formData.append('lang', 'es_ES');"
                        "  formData.append('idRCRD', idRCRD);"
                        "  const response = await fetch('https://www2.agenciatributaria.gob.es/wlpl/DGCO-JDIT/PDFactory', {"
                        "    method: 'POST',"
                        "    body: formData"
                        "  });"
                        "  if (!response.ok) { throw new Error('Network response was not ok'); }"
                        "  return await response.blob();"
                        "}",
                        data_aeat_id,
                    )
                    pdf_path = pdf_files_directory / f"{data_aeat_id}.pdf"
                    async with aiofiles.open(pdf_path, "wb") as f:
                        await f.write(await response.array_buffer())
                    # Записываем успешный URL в файл
                    with open(csv_file_successful, "a", encoding="utf-8") as f:
                        f.write(f"{url}\n")
                    logger.info(f"PDF успешно скачан для URL: {url}")
                except Exception as e:
                    logger.warning(
                        f"Не удалось скачать PDF для страницы {url}. Ошибка: {e}"
                    )
                    continue

            await context.close()
            await browser.close()
    except Exception as e:
        logger.error(f"Ошибка при обработке URL: {e}")


# Асинхронная функция для сохранения HTML и получения ссылок по XPath
async def single_html_one(url):
    proxies = load_proxies()
    proxy = random.choice(proxies) if proxies else None
    if not proxies:
        logger.info("Прокси не найдено, работа будет выполнена локально.")
    try:
        proxy_config = parse_proxy(proxy) if proxy else None
        async with async_playwright() as p:
            browser = (
                await p.chromium.launch(proxy=proxy_config, headless=False)
                if proxy
                else await p.chromium.launch(headless=False)
            )
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()
            # Переход на страницу и ожидание полной загрузки
            await page.goto(url, timeout=60000, wait_until="networkidle")
            await asyncio.sleep(5)
            page_content = await page.content()
            match = re.search(r'var pdfUrl = "(.*?)";', page_content)

            if match:
                pdf_url = match.group(1).replace("\\/", "/")
                print(f"PDF URL найден: {pdf_url}")

                # Обрабатываем загрузку файла
                async with page.expect_download() as download_info:
                    await page.click(
                        f'a[href="{pdf_url}"]'
                    )  # Эмулируем клик по ссылке для загрузки
                download = await download_info.value

                # Путь к загруженному файлу
                download_path = await download.path()
                await asyncio.sleep(10)
                print(f"Файл успешно загружен: {download_path}")
            else:
                print("PDF URL не найден в HTML-коде страницы.")
            # content = await page.content()
            # html_file_path = (
            #     html_files_directory / f"{url.replace(':', '').replace('/', '_')}.html"
            # )
            # with open(html_file_path, "w", encoding="utf-8") as f:
            #     f.write(content)

        await context.close()
        await browser.close()
    except Exception as e:
        logger.error(f"Ошибка при обработке URL: {e}")


# Функция для парсинга прокси
def parse_proxy(proxy):
    if "@" in proxy:
        protocol, rest = proxy.split("://", 1)
        credentials, server = rest.split("@", 1)
        username, password = credentials.split(":", 1)
        return {
            "server": f"{protocol}://{server}",
            "username": username,
            "password": password,
        }
    else:
        return {"server": f"http://{proxy}"}


# Функция для скачивания PDF
def download_pdf(idRCRD, cookies):
    cookies_dict = {cookie["name"]: cookie["value"] for cookie in cookies}

    headers = {
        "Accept": "*/*",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Connection": "keep-alive",
        "Content-Type": "multipart/form-data; boundary=----WebKitFormBoundaryAlx9X84SqxkAGTMD",
        "DNT": "1",
        "Origin": "https://sede.agenciatributaria.gob.es",
        "Referer": "https://sede.agenciatributaria.gob.es/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    files = {
        "operacion": (None, "GET"),
        "lang": (None, "es_ES"),
        "idRCRD": (None, idRCRD),
    }

    try:
        response = requests.post(
            "https://www2.agenciatributaria.gob.es/wlpl/DGCO-JDIT/PDFactory",
            cookies=cookies_dict,
            headers=headers,
            files=files,
        )
        if response.status_code == 200:
            pdf_path = pdf_files_directory / f"{idRCRD}.pdf"
            with open(pdf_path, "wb") as f:
                f.write(response.content)
            # Записываем успешный URL в файл
            with open(csv_file_successful, "a", encoding="utf-8") as f:
                f.write(f"{idRCRD}\n")
            logger.info(f"PDF успешно скачан для idRCRD: {idRCRD}")
        else:
            logger.warning(
                f"Не удалось скачать PDF для idRCRD {idRCRD}. Статус ответа: {response.status_code}"
            )
    except Exception as e:
        logger.error(f"Ошибка при скачивании PDF для idRCRD {idRCRD}: {e}")


# Функция для выполнения основной логики
def main():
    # urls = get_urls(output_csv_file)
    # asyncio.run(single_html(urls))
    url = "https://ejournal.ipinternasional.com/index.php/ijphe/article/view/869/799"
    asyncio.run(single_html_one(url))


if __name__ == "__main__":
    main()
