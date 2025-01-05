from curl_cffi.requests import AsyncSession
import glob
import json
import asyncio
import pandas as pd
from pathlib import Path
import platform

# Получаем текущую директорию
current_directory = Path.cwd()
temp_path = current_directory / "temp"
html_path = temp_path / "html"

# Создание директории, если она не существует
temp_path.mkdir(parents=True, exist_ok=True)
html_path.mkdir(parents=True, exist_ok=True)


def proxy_generator(proxies):
    num_proxies = len(proxies)
    index = 0
    while True:
        proxy = proxies[index]
        yield proxy
        index = (index + 1) % num_proxies


# Загрузить прокси-серверы из файла
def load_proxies_curl_cffi():
    filename = "proxi.json"
    with open(filename, "r") as f:
        raw_proxies = json.load(f)

    formatted_proxies = []
    for proxy in raw_proxies:
        ip, port, username, password = proxy
        formatted_proxies.append(f"http://{username}:{password}@{ip}:{port}")

    return formatted_proxies


def load_proxies():
    filename = "proxi.json"
    with open(filename, "r") as f:
        return json.load(f)


# Функция для выполнения запроса
async def fetch_url(url, proxy, headers, sem, count):
    async with sem:
        async with AsyncSession() as session:
            filename_html = html_path / f"0{count}.html"
            if not filename_html.exists():

                try:
                    response = await session.get(url, proxy=proxy, headers=headers)
                    response.raise_for_status()
                    src = response.text
                    with open(filename_html, "w", encoding="utf-8") as f:
                        f.write(src)
                except Exception as e:
                    print(f"Failed to fetch {url} with proxy {proxy}: {e}")
                await asyncio.sleep(1)


# Основная функция для распределения URL по прокси и запуска задач
async def get_html():

    tasks = []
    proxies = load_proxies_curl_cffi()
    proxy_count = len(proxies)
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    }
    # Устанавливаем ограничение на количество одновременно выполняемых задач
    sem = asyncio.Semaphore(10)  # Ограничение на 100 одновременно выполняемых задач
    csv_file_path = "urls.csv"
    # Чтение CSV файла
    urls_df = pd.read_csv(csv_file_path)
    for count, url in enumerate(urls_df["url"], start=1):
        proxy = proxies[count % proxy_count]
        tasks.append(fetch_url(url, proxy, headers, sem, count))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    if platform.system().lower() == "windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(get_html())
