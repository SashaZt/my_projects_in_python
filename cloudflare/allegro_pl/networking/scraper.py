import asyncio

from aiohttp import ClientSession
from configuration.config import Config


class Scraper:
    def __init__(self, urls):
        self.urls = urls

    async def fetch(self, url, session):
        payload = {"api_key": Config.API_KEY, "url": url}
        async with session.get(
            "https://api.scraperapi.com/", params=payload
        ) as response:
            if response.status == 200:
                return await response.text()

    async def fetch_all(self):
        async with ClientSession() as session:
            tasks = [self.fetch(url, session) for url in self.urls]
            return await asyncio.gather(*tasks)

    def run(self):
        return asyncio.run(self.fetch_all())
