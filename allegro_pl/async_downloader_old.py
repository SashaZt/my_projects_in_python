# import asyncio
# from pathlib import Path

# import aiofiles
# import aiohttp
# import pandas as pd
# from configuration.logger_setup import logger
# from scraperapi_sdk import ScraperAPIClient


# class AsyncDownloader:
#     def __init__(self, api_key, html_files_directory, csv_output_file, max_workers=20):
#         self.api_key = api_key
#         self.client = ScraperAPIClient(self.api_key)
#         self.html_files_directory = html_files_directory
#         self.csv_output_file = csv_output_file
#         self.max_workers = max_workers

#     def get_url_async(self):
#         urls = self.read_cities_from_csv(self.csv_output_file)
#         asyncio.run(self.process_urls(urls))

#     def read_cities_from_csv(self, input_csv_file):
#         df = pd.read_csv(input_csv_file)
#         return df["url"].tolist()

#     async def process_urls(self, urls):
#         # Используем ScraperAPI клиент для пакетных запросов
#         try:
#             async with aiohttp.ClientSession() as session:
#                 tasks = [self.fetch_and_save_html(url, session) for url in urls]
#                 await asyncio.gather(*tasks)
#             logger.info("Асинхронная загрузка завершена.")
#         except Exception as e:
#             logger.error(f"Ошибка при пакетной загрузке URL: {e}")

#     async def fetch_and_save_html(self, url, session):
#         html_company = self.html_files_directory / f"{url.split('/')[-1]}.html"

#         if html_company.exists():
#             logger.warning(f"Файл {html_company} уже существует, пропускаем.")
#             return

#         payload = {"api_key": self.api_key, "url": url}

#         try:
#             async with session.get(
#                 "https://api.scraperapi.com/", params=payload, timeout=30
#             ) as response:
#                 if response.status == 200:
#                     html_content = await response.text()
#                     await self.save_html(html_company, html_content)
#                 else:
#                     logger.warning(f"Ошибка {response.status} при загрузке URL: {url}")
#         except Exception as e:
#             logger.error(f"Ошибка при запросе {url}: {e}")

#     async def save_html(self, file_path, content):
#         try:
#             async with aiofiles.open(file_path, mode="w", encoding="utf-8") as file:
#                 await file.write(content)
#             logger.info(f"Сохранен файл: {file_path}")
#         except Exception as e:
#             logger.error(f"Ошибка при сохранении файла {file_path}: {e}")


import asyncio
from pathlib import Path

import aiofiles
import pandas as pd
from configuration.logger_setup import logger
from scraperapi_sdk import ScraperAPIClient


class AsyncDownloader:
    def __init__(self, api_key, html_files_directory, csv_output_file):
        self.api_key = api_key
        self.client = ScraperAPIClient(self.api_key)
        self.html_files_directory = html_files_directory
        self.csv_output_file = csv_output_file

    def get_url_async(self):
        urls = self.read_cities_from_csv(self.csv_output_file)
        asyncio.run(self.process_batch_urls(urls))

    def read_cities_from_csv(self, input_csv_file):
        df = pd.read_csv(input_csv_file)
        return df["url"].tolist()

    async def process_batch_urls(self, urls):
        try:
            # Отправляем пакетный запрос на ScraperAPI
            response = await self.client.batch(urls)
            tasks = []

            for result in response["results"]:
                if result["statusCode"] == 200:
                    html_company = (
                        self.html_files_directory
                        / f"{result['url'].split('/')[-1]}.html"
                    )
                    tasks.append(self.save_html(html_company, result["content"]))
                else:
                    logger.warning(
                        f"Ошибка {result['statusCode']} при загрузке URL: {result['url']}"
                    )

            await asyncio.gather(*tasks)
            logger.info("Асинхронная загрузка завершена.")
        except Exception as e:
            logger.error(f"Ошибка при пакетной загрузке URL: {e}")

    async def save_html(self, file_path, content):
        try:
            async with aiofiles.open(file_path, mode="w", encoding="utf-8") as file:
                await file.write(content)
            logger.info(f"Сохранен файл: {file_path}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении файла {file_path}: {e}")
