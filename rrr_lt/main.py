import asyncio
import json
from pathlib import Path
from typing import Optional, Dict
import random
import aiofiles
from playwright.async_api import async_playwright, Response
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, url: str):
        self.url = url
        self.current_directory = Path.cwd()
        self.proxy_file = self.current_directory / "configuration" / "roman.txt"
        self.json_file = self.current_directory / "data" / "response.json"
        self.setup_directories()

    def setup_directories(self):
        """Создание необходимых директорий."""
        (self.current_directory / "configuration").mkdir(parents=True, exist_ok=True)
        (self.current_directory / "data").mkdir(parents=True, exist_ok=True)
        logger.info("Directories created or already exist")

    async def load_proxies(self) -> list:
        """Загрузка прокси из файла."""
        if not self.proxy_file.exists():
            logger.info(f"Proxy file {self.proxy_file} not found. Running locally.")
            return []
        
        try:
            async with aiofiles.open(self.proxy_file, 'r', encoding='utf-8') as file:
                proxies = [line.strip() for line in await file.readlines() if line.strip()]
            logger.info(f"Loaded {len(proxies)} proxies")
            return proxies
        except Exception as e:
            logger.error(f"Error loading proxies: {e}")
            return []

    def parse_proxy(self, proxy: str) -> Dict:
        """Парсинг строки прокси в конфигурацию."""
        try:
            if "@" in proxy:
                protocol, rest = proxy.split("://", 1)
                credentials, server = rest.split("@", 1)
                username, password = credentials.split(":", 1)
                return {
                    "server": f"{protocol}://{server}",
                    "username": username,
                    "password": password,
                }
            return {"server": f"http://{proxy}"}
        except Exception as e:
            logger.error(f"Error parsing proxy {proxy}: {e}")
            return None

    async def save_json_response(self, data: dict):
        """Сохранение JSON ответа в файл."""
        try:
            async with aiofiles.open(self.json_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            logger.info(f"JSON response saved to {self.json_file}")
        except Exception as e:
            logger.error(f"Error saving JSON response: {e}")

    async def handle_response(self, response: Response):
        """Обработка ответов от сервера."""
        try:
            if "rrr.lt/ru/poisk?q" in response.url:
                headers = await response.all_headers()
                if 'application/json' in headers.get('content-type', ''):
                    logger.info(f"Intercepted JSON response from {response.url}")
                    json_data = await response.json()
                    await self.save_json_response(json_data)
                    logger.info("JSON response captured and saved")
        except Exception as e:
            logger.error(f"Error handling response: {e}")

    async def scrape(self):
        """Основной метод скрапинга."""
        proxies = await self.load_proxies()
        retry_count = 3
        
        for attempt in range(retry_count):
            try:
                proxy_config = None
                if proxies:
                    proxy = random.choice(proxies)
                    proxy_config = self.parse_proxy(proxy)
                    logger.info(f"Using proxy: {proxy}")
                else:
                    logger.info("Running without proxy")

                async with async_playwright() as p:
                    browser_args = {
                        "headless": False,  # Показывать браузер
                    }
                    
                    if proxy_config:
                        browser_args["proxy"] = proxy_config
                    
                    browser = await p.chromium.launch(**browser_args)
                    context = await browser.new_context(
                        viewport={'width': 1920, 'height': 1080}
                    )
                    page = await context.new_page()
                    
                    # Подписываемся на события ответа
                    page.on("response", self.handle_response)
                    
                    try:
                        logger.info(f"Navigating to URL: {self.url}")
                        response = await page.goto(
                            self.url,
                            timeout=30000,
                            wait_until="networkidle"
                        )
                        
                        if response.status == 403:
                            logger.warning("Access denied (403)")
                            if proxies:
                                logger.info(f"Retrying with different proxy. Attempt {attempt + 1}/{retry_count}")
                                continue
                        
                        # Ждем загрузки контента и возможных AJAX запросов
                        await asyncio.sleep(5)
                        
                        logger.info(f"Final URL: {page.url}")
                        logger.info(f"Status: {response.status}")
                        
                        return True
                        
                    except Exception as e:
                        logger.error(f"Error during navigation: {e}")
                        if attempt < retry_count - 1:
                            logger.info(f"Retrying... Attempt {attempt + 2}/{retry_count}")
                            continue
                        raise
                    finally:
                        await context.close()
                        await browser.close()
                        
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == retry_count - 1:
                    raise
                
        return False

def main():
    url = "https://rrr.lt/ru/poisk?q=K6D39U438AD"
    scraper = WebScraper(url)
    
    try:
        success = asyncio.run(scraper.scrape())
        if success:
            logger.info("Scraping completed successfully")
        else:
            logger.error("Scraping failed after all retries")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()