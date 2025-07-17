import asyncio
import csv
from urllib.parse import urljoin

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
from downloader import downloader

from config import Config, logger, paths


class ProcurementScraper:
    def __init__(self):
        self.base_url = "https://procurement.kg"
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "DNT": "1",
            "Referer": "https://procurement.kg/suppliers-list",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-gpc": "1",
        }
        self.cookies = {"astratop": "1"}
        self.all_urls = []

    async def fetch_page(self, session, page_num):
        """Получает HTML страницы"""
        if page_num == 1:
            url = "https://procurement.kg/suppliers-list"
        else:
            url = f"https://procurement.kg/suppliers-list/page/{page_num}"

        try:
            async with session.get(
                url, headers=self.headers, cookies=self.cookies
            ) as response:
                # Игнорируем статус 500, если есть контент
                if response.status == 500:
                    logger.warning(
                        f"Получен статус 500 для страницы {page_num}, но продолжаем обработку"
                    )

                content = await response.text()
                logger.info(
                    f"Страница {page_num} загружена (статус: {response.status})"
                )
                return content, page_num

        except Exception as e:
            logger.error(f"Ошибка при загрузке страницы {page_num}: {e}")
            return None, page_num

    def extract_urls(self, html_content):
        """Извлекает URLs из HTML контента"""
        soup = BeautifulSoup(html_content, "html.parser")
        urls = []

        # Ищем все элементы с классом tender-item
        tender_items = soup.find_all("li", class_="tender-item")

        for item in tender_items:
            # Ищем ссылку в заголовке
            title_link = item.find("h4", class_="supp-title-list")
            if title_link:
                link = title_link.find("a")
                if link and link.get("href"):
                    url = link.get("href")
                    # Проверяем, что это полный URL
                    if url.startswith("http"):
                        urls.append(url)
                    else:
                        # Если относительный URL, делаем его абсолютным
                        full_url = urljoin(self.base_url, url)
                        urls.append(full_url)

        return urls

    async def scrape_page(self, session, page_num):
        """Собирает URLs с одной страницы"""
        html_content, page = await self.fetch_page(session, page_num)

        if html_content:
            urls = self.extract_urls(html_content)
            logger.info(f"Со страницы {page} собрано {len(urls)} URLs")
            return urls
        else:
            logger.warning(f"Не удалось получить контент страницы {page}")
            return []

    async def scrape_all_pages(self, max_pages=25):
        """Собирает URLs со всех страниц"""
        connector = aiohttp.TCPConnector(limit=5, limit_per_host=3, ssl=False)

        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            # Создаем задачи для всех страниц
            tasks = []
            for page_num in range(1, max_pages + 1):
                task = asyncio.create_task(self.scrape_page(session, page_num))
                tasks.append(task)

                # Добавляем небольшую задержку между запросами
                await asyncio.sleep(0.1)

            # Выполняем все задачи
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Собираем все URLs
            for result in results:
                if isinstance(result, list):
                    self.all_urls.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Ошибка при обработке: {result}")

    def save_to_csv(self, filename="urls.csv"):
        """Сохраняет URLs в CSV файл"""
        try:
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["url"])  # Заголовок

                for url in self.all_urls:
                    writer.writerow([url])

            logger.info(f"Сохранено {len(self.all_urls)} URLs в файл {filename}")

        except Exception as e:
            logger.error(f"Ошибка при сохранении в CSV: {e}")

    async def run(self, max_pages=25):
        """Основная функция для запуска скрапинга"""
        logger.info(f"Начинаем сбор URLs с {max_pages} страниц")

        await self.scrape_all_pages(max_pages)

        if self.all_urls:
            # Удаляем дубликаты
            unique_urls = list(set(self.all_urls))
            self.all_urls = unique_urls

            logger.info(f"Всего собрано уникальных URLs: {len(self.all_urls)}")
            self.save_to_csv()
        else:
            logger.warning("Не удалось собрать URLs")


async def main():
    scraper = ProcurementScraper()
    await scraper.run(25)  # Собираем с 25 страниц


if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(downloader.download_from_csv("urls.csv"))
