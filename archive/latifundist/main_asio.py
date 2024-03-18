import asyncio
import aiohttp

header = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}

async def fetch_page(session, url):
    async with session.get(url, headers=header) as response:
        return await response.text()

async def download_pages():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(1, 1158):
            url = f"https://latifundist.com/birzha?rid=0&page={i}"
            task = asyncio.ensure_future(fetch_page(session, url))
            tasks.append(task)
        pages = await asyncio.gather(*tasks)
        for i, page in enumerate(pages):
            with open(f"data/data_0{i+1:03}.html", "w", encoding="utf-8") as file:
                file.write(page)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(download_pages())
