import ast
import asyncio
import json
import logging
import os
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import demjson3
import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from dotenv import load_dotenv

env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)
api_key = os.getenv("API_KEY")
# Настройте максимальное количество попыток, если требуется
MAX_RETRIES = 30
RETRY_DELAY = 30  # Задержка между попытками в секундах

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
xml_directory = current_directory / "xml_file"
html_directory = current_directory / "html"
json_directory = current_directory / "json"
xml_files_directory = current_directory / "xml_files"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(exist_ok=True, parents=True)
json_directory.mkdir(exist_ok=True, parents=True)
xml_directory.mkdir(exist_ok=True, parents=True)
xml_files_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)


start_sitemap = xml_directory / "sitemap.xml"
all_urls_page = data_directory / "all_urls.csv"
all_url_sitemap = data_directory / "sitemap.csv"


def read_csv(file):
    # Читаем файл start_sitemap.csv и возвращаем список URL
    df = pd.read_csv(file)
    return df["url"].tolist()


# # Функция для отправки задач на ScraperAPI в пакетном режиме
# def submit_jobs():
#     urls = read_csv(all_urls_page)  # Чтение всех URL из CSV
#     batch_size = 50000  # Максимальный размер пакета (по документации)
#     # Разбиваем список URL на части по batch_size
#     for i in range(0, len(urls), batch_size):
#         url_batch = urls[i : i + batch_size]  # Создаем очередной пакет URL
#         headers = {
#             "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
#             "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
#         }
#         # Формируем тело запроса
#         data = {
#             "apiKey": api_key,
#             "urls": url_batch,  # Передаём текущий пакет URL
#             "apiParams": {
#                 "keep_headers": "true",
#                 "device_type": "desktop",
#                 "headers": headers,
#             },
#         }
#         # Отправляем запрос на создание пакетной задачи
#         response = requests.post(
#             url="https://async.scraperapi.com/batchjobs", json=data, timeout=30
#         )
#         if response.status_code == 200:
#             response_data = response.json()
#             for job in response_data:
#                 job_id = job.get("id")
#                 json_file = json_directory / f"{job_id}.json"
#                 # Сохраняем информацию о каждой задаче в отдельный JSON файл
#                 with open(json_file, "w", encoding="utf-8") as file:
#                     json.dump(job, file, indent=4)
#                 logger.info(
#                     f"Пакетная задача отправлена для URL из пакета, начиная с индекса {i}"
#                 )
#         else:
#             logger.error(f"Ошибка при отправке пакетной задачи: {response.status_code}")


def submit_jobs():
    urls = read_csv(all_urls_page)  # Чтение всех URL из CSV
    batch_size = 50000  # Максимальный размер пакета (по документации)

    # Разбиваем список URL на части по batch_size
    for i in range(0, len(urls), batch_size):
        url_batch = []
        for url in urls[i : i + batch_size]:  # Формируем очередной пакет URL
            # Формирование имени файла
            url_parts = url.split("/")
            last_part = url_parts[-1].split("?")  # Разделяем последний сегмент по '?'

            # Основная часть имени
            base_name = "_".join(
                part.replace("-", "_") for part in url_parts[-3:-1]
            )  # Берём последние три части URL (без query string)

            # Обработка query string (если есть)
            if len(last_part) > 1:
                query_part = last_part[1].replace("=", "_").replace("-", "_")
                file_name = (
                    f"{base_name}_{last_part[0].replace('-', '_')}_{query_part}.html"
                )
            else:
                file_name = f"{base_name}_{last_part[0].replace('-', '_')}.html"

            html_output_file = html_directory / file_name

            # Проверка существования HTML-файла
            if html_output_file.exists():
                # logger.info(
                #     f"Файл {html_output_file} уже существует, пропускаем URL: {url}"
                # )
                continue

            # Добавляем URL в пакет, если файл не существует
            url_batch.append(url)

        # Если пакет пустой, пропускаем отправку
        if not url_batch:
            logger.info(f"Все URL из текущего пакета (индекс {i}) уже обработаны.")
            continue

        # Формируем заголовки для запроса
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "ru,en;q=0.9,uk;q=0.8",
            "cache-control": "no-cache",
            "dnt": "1",  # Для анонимного доступа
            "pragma": "no-cache",  # Для предотвращения кэширования
            "sec-fetch-dest": "document",  # Это указывает, что вы запрашиваете HTML-документ
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "upgrade-insecure-requests": "1",  # Обеспечивает безопасное соединение
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }

        # Формируем тело запроса
        data = {
            "apiKey": api_key,
            "urls": url_batch,  # Передаём пакет URL
            "apiParams": {
                "keep_headers": "true",
                "device_type": "desktop",
                "headers": headers,
            },
        }

        # Отправляем запрос на создание пакетной задачи
        response = requests.post(
            url="https://async.scraperapi.com/batchjobs", json=data, timeout=30
        )

        # Обработка ответа от API
        if response.status_code == 200:
            response_data = response.json()
            for job in response_data:
                job_id = job.get("id")
                json_file = json_directory / f"{job_id}.json"
                # Сохраняем информацию о каждой задаче в отдельный JSON файл
                with open(json_file, "w", encoding="utf-8") as file:
                    json.dump(job, file, indent=4)
                logger.info(f"Пакетная задача отправлена для URL: {job.get('url')}")
        else:
            logger.error(f"Ошибка при отправке пакетной задачи: {response.status_code}")


async def fetch_results_async():
    while True:
        all_finished = True
        for json_file in json_directory.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as file:
                    response_data = json.load(file)
                status_url = response_data.get("statusUrl")  # URL для проверки статуса
                try:
                    response = requests.get(url=status_url, timeout=30)
                except requests.exceptions.ReadTimeout:
                    break
                except requests.exceptions.SSLError as e:
                    break
                except requests.exceptions.RequestException as e:
                    break
                except Exception as e:
                    break
                if response.status_code == 200:
                    job_status = response.json().get("status")
                    if job_status == "finished":  # Если задача завершена
                        url = response_data.get("url")
                        body = response.json().get("response").get("body")

                        # Убедимся, что body является строкой
                        if isinstance(body, dict):
                            body = json.dumps(body, indent=4, ensure_ascii=False)

                        # Генерируем имя файла на основе URL
                        url_parts = url.split("/")
                        last_part = url_parts[-1].split("?")
                        base_name = "_".join(
                            part.replace("-", "_") for part in url_parts[-3:-1]
                        )
                        file_name = f"{base_name}_{last_part[0].replace('-', '_')}.html"
                        html_company = html_directory / file_name

                        # Сохраняем результат в файл
                        with open(html_company, "w", encoding="utf-8") as file:
                            file.write(body)
                        logger.info(
                            f"Результаты для {status_url} сохранены в файл {html_company}"
                        )
                        try:
                            json_file.unlink()  # Удаляем JSON файл после сохранения результата
                        except PermissionError as e:
                            logger.error(f"Не удалось удалить файл {json_file}: {e}")
                    else:
                        all_finished = False
                        logger.info(f"Статус задачи для {status_url}: {job_status}")
                else:
                    logger.error(
                        f"Ошибка при получении статуса задачи для {status_url}: {response.status_code}"
                    )
            except PermissionError as e:
                logger.error(f"Не удалось открыть файл {json_file}: {e}")

        if all_finished:
            break
        await asyncio.sleep(10)  # Ждём 10 секунд перед повторной проверкой


# Основная функция для скачивания все товаров
async def main_url():
    # Проверка наличия файлов в json_files_directory
    if any(json_directory.glob("*.json")):
        # Получение результатов задач, если есть несохраненные результаты
        await fetch_results_async()
    else:
        # Отправка задач на ScraperAPI, если json файлов нет
        submit_jobs()
        # Получение результатов задач
        await fetch_results_async()


if __name__ == "__main__":
    while True:
        asyncio.run(main_url())
        time.sleep(10)
