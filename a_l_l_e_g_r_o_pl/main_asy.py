import asyncio
import json
import logging
import os
import time
from pathlib import Path

import pandas as pd
import requests
from configuration.logger_setup import logger
from dotenv import load_dotenv

# Загрузка переменных окружения
env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)
api_key = os.getenv("API_KEY")

# Директории для сохранения файлов
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
json_files_directory = current_directory / "json"
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
json_files_directory.mkdir(exist_ok=True, parents=True)
csv_output_file = data_directory / "output.csv"


# Функция для чтения городов из CSV файла
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


# Функция для отправки задач на ScraperAPI
def submit_jobs():
    urls = read_cities_from_csv(csv_output_file)
    for url in urls:

        html_company = html_files_directory / f"{url.split('/')[-1]}.html"
        # Если файл HTML уже существует, удаляем JSON файл и пропускаем
        if html_company.exists():
            logger.warning(f"Файл {html_company} уже существует, пропускаем.")
            continue

        response = requests.post(
            url="https://async.scraperapi.com/jobs",
            json={"apiKey": api_key, "url": url},
            timeout=30,
        )
        if response.status_code == 200:
            response_data = response.json()
            job_id = response_data.get("id")
            json_file = json_files_directory / f"{job_id}.json"
            with open(json_file, "w", encoding="utf-8") as file:
                json.dump(response_data, file, indent=4)
            logger.info(
                f"Задача отправлена для URL {url}, статус доступен по адресу: {response_data.get('statusUrl')}"
            )
        else:
            logger.error(
                f"Ошибка при отправке задачи для URL {url}: {response.status_code}"
            )


# Функция для получения результатов задач и сохранения в файл
async def fetch_results_async():
    while True:
        all_finished = True
        for json_file in json_files_directory.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as file:
                    response_data = json.load(file)
                html_company = (
                    html_files_directory
                    / f"{response_data.get('url').split('/')[-1]}.html"
                )
                # Если файл HTML уже существует, удаляем JSON файл и пропускаем
                if html_company.exists():
                    logger.info(
                        f"Файл {html_company} уже существует, удаляем JSON файл и пропускаем."
                    )
                    try:
                        json_file.unlink()
                    except PermissionError as e:
                        logger.error(f"Не удалось удалить файл {json_file}: {e}")
                    continue

                status_url = response_data.get("statusUrl")
                response = requests.get(url=status_url, timeout=30)
                if response.status_code == 200:
                    job_status = response.json().get("status")
                    if job_status == "finished":
                        body = response.json().get("response").get("body")
                        with open(html_company, "w", encoding="utf-8") as file:
                            file.write(body)
                        logger.info(
                            f"Результаты для {status_url} сохранены в файл {html_company}"
                        )
                        # Удаление JSON файла после успешного сохранения результата
                        try:
                            json_file.unlink()
                        except PermissionError as e:
                            logger.error(f"Не удалось удалить файл {json_file}: {e}")
                    else:
                        all_finished = False
                        logger.info(f"Статус задачи для {status_url}: {job_status}")
                else:
                    logger.error(
                        f"Ошибка при получении статуса задачи: {response.status_code}"
                    )
            except PermissionError as e:
                logger.error(f"Не удалось открыть файл {json_file}: {e}")
        if all_finished:
            break
        await asyncio.sleep(10)  # Подождите 10 секунд перед повторной проверкой


# Основная функция
async def main():
    # Проверка наличия файлов в json_files_directory
    if any(json_files_directory.glob("*.json")):
        # Получение результатов задач, если есть несохраненные результаты
        await fetch_results_async()
    else:
        # Отправка задач на ScraperAPI, если json файлов нет
        submit_jobs()
        # Получение результатов задач
        await fetch_results_async()


# Запуск программы
if __name__ == "__main__":
    asyncio.run(main())
