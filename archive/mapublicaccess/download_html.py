import asyncio
import aiohttp
import aiofiles
import time
import sys
import json
from asyncio import sleep
import os


def load_config_headers():
    if getattr(sys, "frozen", False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "config.json")
    if not os.path.exists(filename_config):
        print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
        sys.exit(1)
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)
    headers = config["headers"]

    if "cookies" in config:
        cookies_str = "; ".join([f"{k}={v}" for k, v in config["cookies"].items()])
        headers["Cookie"] = cookies_str
    return config
config = load_config_headers()

async def create_directories_async(folders_list):
    for folder in folders_list:
        if not os.path.exists(folder):
            os.makedirs(folder)


async def read_csv_and_return_values(filename: str):
    unique_values = set()
    async with aiofiles.open(filename, mode="r", encoding="utf-8") as file:
        async for line in file:
            value = line.strip()
            unique_values.add(value)
    return list(unique_values)


async def fetch_with_aiohttp(config):

    headers = config["headers"]

    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    csv_path = os.path.join(temp_path, "pdf")
    html_path = os.path.join(temp_path, "html")

    data_list = await read_csv_and_return_values("MA199_A.csv")

    for pin in data_list:
        filename_html = os.path.join(html_path, f"{pin}.html")
        if not os.path.exists(filename_html):
            params = {
                "pin": pin,
                "gsp": "PROFILEALL",
                "taxyear": "2024",
                "jur": "MA199",
                "ownseq": "0",
                "card": "1",
                "roll": "RP",
                "State": "1",
                "item": "1",
                "items": "-1",
                "all": "all",
                "ranks": "Datalet",
            }
            url = "https://mapublicaccess.tylerhost.net/Datalets/PrintDatalet.aspx"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    
                        if response.status == 200:

                            html_content = await response.text()
                            await save_html_to_file(filename_html, html_content)
                            await asyncio.sleep(5)
                        else:
                            print(f"Ошибка запроса: {response.status} на {pin}")
                            print("ОБВНОВИ cookies!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            return None
        else:
            continue

async def save_html_to_file(file_path, html_content):
    async with aiofiles.open(file_path, "w", encoding="utf-8") as file:
        await file.write(html_content)


asyncio.run(fetch_with_aiohttp(config))
