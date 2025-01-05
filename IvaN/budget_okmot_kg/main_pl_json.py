import asyncio
import json
import random
from pathlib import Path

import aiofiles
from configuration.logger_setup import logger
from playwright.async_api import async_playwright


class WebScraper:
    def __init__(self, url):
        self.url = url
        self.current_directory = Path.cwd()
        self.data_directory = self.current_directory / "data"
        self.configuration_directory = self.current_directory / "configuration"
        self.json_responses_directory = self.current_directory / "json_responses"
        self.file_json = self.json_responses_directory / "post_response.json"
        self.file_proxy = self.configuration_directory / "roman.txt"
        self._setup_directories()

    def _setup_directories(self):
        self.data_directory.mkdir(parents=True, exist_ok=True)
        self.configuration_directory.mkdir(parents=True, exist_ok=True)
        logger.info("Директории для данных созданы или уже существуют.")

    def load_proxies(self):
        logger.info("Загрузка списка прокси...")
        if not Path(self.file_proxy).exists():
            logger.warning(
                f"Файл с прокси {self.file_proxy} не найден. Работаем без прокси."
            )
            return []
        with open(self.file_proxy, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in file]
        logger.info(f"Загружено {len(proxies)} прокси.")
        return proxies

    async def log_post_response(self, response):
        logger.info("Обработка POST ответа...")
        if (
            response.request.method == "GET"
            and "https://budget.okmot.kg/api/income" in response.url
        ):
            try:
                json_response = await response.json()
                await self.save_response_json(json_response, self.file_json)
                logger.info(f"POST response saved to {self.file_json}")
            except Exception as e:
                logger.error(f"Failed to process POST response: {e}")

    async def single_html_json(self):
        logger.info(f"Начало обработки URL: {self.url}")
        proxies = self.load_proxies()
        proxy_config = None
        if proxies:
            proxy = random.choice(proxies)
            proxy_config = self.parse_proxy(proxy)
            logger.info(f"Используем прокси: {proxy}")
        else:
            logger.info("Прокси не используется.")
        try:
            async with async_playwright() as p:
                logger.info("Запуск браузера...")
                browser = await p.chromium.launch(proxy=proxy_config, headless=False)
                context = await browser.new_context()
                page = await context.new_page()
                page.on("response", self.log_post_response)

                logger.info("Отключение медиа ресурсов...")
                await page.route(
                    "**/*",
                    lambda route: (
                        route.abort()
                        if route.request.resource_type in ["image", "media"]
                        else route.continue_()
                    ),
                )

                logger.info(f"Переход на страницу: {self.url}")
                await page.goto(self.url, timeout=100000, wait_until="networkidle")

                logger.info("Закрытие контекста и браузера...")
                await context.close()
                await browser.close()
        except Exception as e:
            logger.error(f"Ошибка при обработке {self.url}: {e}")

    async def save_response_json(self, json_response, file_path):
        logger.info(f"Сохранение JSON данных в файл: {file_path}")
        async with aiofiles.open(file_path, mode="w", encoding="utf-8") as f:
            await f.write(json.dumps(json_response, ensure_ascii=False, indent=4))
        logger.info("JSON данные успешно сохранены.")

    def parse_proxy(self, proxy):
        logger.info(f"Парсинг прокси: {proxy}")
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

    def run(self):
        logger.info("Запуск основной функции...")
        asyncio.run(self.single_html_json())
        logger.info("Основная функция завершена.")


if __name__ == "__main__":
    url = "https://budget.okmot.kg/api/income/tin?tin=00000000000000&year=2021&startMonth=1&endMonth=12"
    scraper = WebScraper(url)
    scraper.run()
