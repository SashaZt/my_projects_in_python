import asyncio
import json
import logging
import time
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class AsyncBatchScraper:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        headers: Dict,
        cookies: Dict,
        json_product_directory: Path,
        max_retries: int = 10,
        delay: int = 30,
        batch_size: int = 50,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = headers
        self.cookies = cookies
        self.json_product_directory = json_product_directory
        self.max_retries = max_retries
        self.delay = delay
        self.batch_size = batch_size

        # Формируем строку Cookie из словаря cookies
        cookie_string = "; ".join(f"{key}={value}" for key, value in cookies.items())
        self.headers["Cookie"] = cookie_string

    async def check_job_status(
        self, session: aiohttp.ClientSession, status_url: str
    ) -> Optional[dict]:
        """Проверяет статус задания и возвращает результат"""
        retries = 0
        while retries < self.max_retries:
            try:
                async with session.get(status_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["status"] == "finished":
                            return data
                        elif data["status"] == "failed":
                            logger.error(f"Job failed for URL: {status_url}")
                            return None
                    await asyncio.sleep(self.delay)
            except Exception as e:
                logger.error(f"Error checking job status: {e}")
                retries += 1
                await asyncio.sleep(self.delay)
        return None

    async def process_batch(
        self, session: aiohttp.ClientSession, id_products: List[str]
    ) -> None:
        """Обрабатывает пакет ID продуктов"""
        # Подготовка URLs для batch запроса
        urls = []
        for id_product in id_products:
            query_params = {"q": id_product, "prs": "2", "page": "1"}
            full_url = f"{self.base_url}?{urllib.parse.urlencode(query_params)}"
            urls.append(full_url)

        # Формируем batch запрос
        batch_data = {
            "apiKey": self.api_key,
            "urls": urls,
            "apiParams": {"keep_headers": True},
            "headers": self.headers,
        }

        try:
            async with session.post(
                "https://async.scraperapi.com/batchjobs", json=batch_data
            ) as response:
                if response.status == 200:
                    jobs = await response.json()

                    # Ждем завершения всех jobs и получаем результаты
                    tasks = [
                        self.check_job_status(session, job["statusUrl"]) for job in jobs
                    ]
                    results = await asyncio.gather(*tasks)

                    # Сохраняем результаты
                    for id_product, result in zip(id_products, results):
                        if result and "response" in result:
                            json_file = (
                                self.json_product_directory / f"{id_product}.json"
                            )
                            if not json_file.exists():
                                with open(json_file, "w", encoding="utf-8") as f:
                                    json.dump(result["response"], f, ensure_ascii=False)
                                logger.info(f"Сохранен файл {json_file}")
                            else:
                                logger.info(
                                    f"Файл {json_file} уже существует. Пропущен."
                                )
                        else:
                            logger.error(f"Не удалось получить данные для {id_product}")
                else:
                    logger.error(
                        f"Ошибка при создании batch задания: {response.status}"
                    )
        except Exception as e:
            logger.error(f"Ошибка при обработке batch запроса: {e}")

    async def process_all_products(self, id_products: List[str]) -> None:
        """Обрабатывает все ID продуктов с использованием batch запросов"""
        async with aiohttp.ClientSession() as session:
            # Разбиваем список на батчи
            for i in range(0, len(id_products), self.batch_size):
                batch = id_products[i : i + self.batch_size]
                await self.process_batch(session, batch)
                await asyncio.sleep(1)  # Небольшая пауза между батчами


def get_all_pages_html_async(
    id_products: List[str],
    api_key: str,
    base_url: str,
    headers: Dict,
    cookies: Dict,
    json_product_directory: Path,
    max_retries: int = 10,
    delay: int = 30,
    batch_size: int = 50,
) -> None:
    """
    Асинхронная версия get_all_page_html для обработки множества ID продуктов
    """
    scraper = AsyncBatchScraper(
        api_key=api_key,
        base_url=base_url,
        headers=headers,
        cookies=cookies,
        json_product_directory=json_product_directory,
        max_retries=max_retries,
        delay=delay,
        batch_size=batch_size,
    )

    asyncio.run(scraper.process_all_products(id_products))


id_products = ["product1", "product2", "product3"]
get_all_pages_html_async(
    id_products=id_products,
    api_key=API_KEY,
    base_url="https://rrr.lt/ru/poisk",
    headers=HEADERS,
    cookies=COOKIES,
    json_product_directory=json_product_directory,
    max_retries=MAX_RETRIES,
    delay=RETRY_DELAY,
    batch_size=50,
)
