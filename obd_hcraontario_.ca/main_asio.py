import aiohttp
import asyncio
import os
import json
import json
import re
import csv
import requests
import os
import glob
import random
import aiohttp
import asyncio
import os
import json
import random
from aiofiles import open as aio_open
from proxi import proxies

current_directory = os.getcwd()
temp_directory = "temp"
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
summary_path = os.path.join(temp_directory, "summary")
contact_path = os.path.join(temp_directory, "contact")
import aiofiles  # Импортируем асинхронную библиотеку для работы с файлами


async def parsing():
    async with aiofiles.open("test.json", "r", encoding="utf-8") as f:
        # Читаем файл как текст асинхронно
        content = await f.read()
    # Преобразуем прочитанный текст в JSON
    data_json = json.loads(content)
    return [d["ACCOUNTNUMBER"] for d in data_json if d.get("LICENSESTATUS") == "Expired"]



def proxy_random():
    proxy = random.choice(proxies)
    proxy_host, proxy_port, proxy_user, proxy_pass = proxy
    formatted_proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
    return {"http": formatted_proxy, "https": formatted_proxy}


async def check_files_exist(account_numbers, save_path):
    """Возвращает список номеров аккаунтов, для которых нет файлов."""
    return [
        num
        for num in account_numbers
        if not os.path.exists(os.path.join(save_path, f"{num}.json"))
    ]


async def fetch_and_save_data(api_url, save_path):
    all_data = await parsing()
    accounts_to_fetch = await check_files_exist(all_data, save_path)

    async with aiohttp.ClientSession() as session:
        for i in range(0, len(accounts_to_fetch), 10):
            current_batch = accounts_to_fetch[i : i + 10]
            tasks = []
            for account_number in current_batch:
                if account_number:  # Проверяем, что account_number не None
                    task = asyncio.create_task(
                        fetch_and_process(session, api_url, account_number, save_path)
                    )
                    tasks.append(task)
                else:
                    print("Обнаружен account_number с недопустимым значением None")
            await asyncio.gather(*tasks)
            await asyncio.sleep(1)


async def fetch_and_process(session, api_url, account_number, save_path):

    all_data = (
        await parsing()
    )  # Убедитесь, что parsing() поддерживает асинхронность, если это необходимо
    async with aiohttp.ClientSession() as session:
        cookies = {
            "ARRAffinity": "7728a9db7a843ce19ed47ff831421589468bd2f1f7c07638fcce4ad2da6697ff",
            "ARRAffinitySameSite": "7728a9db7a843ce19ed47ff831421589468bd2f1f7c07638fcce4ad2da6697ff",
        }

        headers = {
            "authority": "obd.hcraontario.ca",
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
            "cache-control": "no-cache",
            # 'cookie': 'ARRAffinity=7728a9db7a843ce19ed47ff831421589468bd2f1f7c07638fcce4ad2da6697ff; ARRAffinitySameSite=7728a9db7a843ce19ed47ff831421589468bd2f1f7c07638fcce4ad2da6697ff',
            "dnt": "1",
            "pragma": "no-cache",
            "referer": "https://obd.hcraontario.ca/buildersearchresults?&page=1",
            "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }

        params = {"id": account_number}
        filename = os.path.join(save_path, f"{params['id']}.json")

        if not os.path.exists(filename):
            proxies = proxy_random()  # Получаем прокси
            async with session.get(
                api_url,
                params=params,
                cookies=cookies,
                headers=headers,
                proxy=proxies["http"],
            ) as response:
                if response.status == 200:
                    json_data = await response.json()
                    async with aiofiles.open(filename, "w", encoding="utf-8") as f:
                        await f.write(
                            json.dumps(json_data, ensure_ascii=False, indent=4)
                        )


async def main():
    url_summary = "https://obd.hcraontario.ca/api/buildersummary"
    url_contact = "https://obd.hcraontario.ca/api/builderPDOs"
    await asyncio.gather(
        fetch_and_save_data(url_summary, summary_path),
        fetch_and_save_data(url_contact, contact_path),
    )


if __name__ == "__main__":
    asyncio.run(main())
