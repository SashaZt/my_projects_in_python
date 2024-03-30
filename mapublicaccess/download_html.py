from typing import List

import asyncio
from math import e
from time import sleep
from playwright.async_api import async_playwright
import aiohttp
import aiofiles
import re
import string

import os
import glob
from asyncio import sleep
import requests
import csv
import aiohttp
import aiofiles
import os


async def create_directories_async(folders_list):
    for folder in folders_list:
        if not os.path.exists(folder):
            os.makedirs(folder)


async def read_csv_and_return_values(filename: str):
    unique_values = set()  # Используем множество для хранения уникальных значений
    async with aiofiles.open(filename, mode='r', encoding='utf-8') as file:
        async for line in file:
            value = line.strip()  # Убираем пробельные символы с начала и конца строки
            unique_values.add(value)  # Добавляем значение в множество уникальных значений
    return list(unique_values)  # Возвращаем список уникальных значений



def main():

    cookies = {
        "ASP.NET_SessionId": "fqlxp3hq23tyo2bot0upbgj2",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # 'Cookie': 'ASP.NET_SessionId=fqlxp3hq23tyo2bot0upbgj2',
        "DNT": "1",
        "Pragma": "no-cache",
        "Referer": "https://mapublicaccess.tylerhost.net/Datalets/Datalet.aspx?sIndex=1&idx=1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    params = {
        "pin": "1990060000800000",
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
    response = requests.get(
        url,
        params=params,
        cookies=cookies,
        headers=headers,
    )


async def fetch_with_aiohttp():
    # Создайте полный путь к папке temp
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    csv_path = os.path.join(temp_path, "pdf")
    html_path = os.path.join(temp_path, "html")

    data_list = await read_csv_and_return_values("MA199_A.csv")
    cookies = {
        "ASP.NET_SessionId": "fqlxp3hq23tyo2bot0upbgj2",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # 'Cookie': 'ASP.NET_SessionId=fqlxp3hq23tyo2bot0upbgj2',
        "DNT": "1",
        "Pragma": "no-cache",
        "Referer": "https://mapublicaccess.tylerhost.net/Datalets/Datalet.aspx?sIndex=1&idx=1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    for pin in data_list:
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
            async with session.get(
                url, params=params, cookies=cookies, headers=headers
            ) as response:
                # Проверяем статус ответа
                filename_html = os.path.join(html_path, f"{pin}.html")
                if not os.path.exists(filename_html):
                    if response.status == 200:
                        # Возвращаем текст ответа
                        
                        html_content = await response.text()
                        await save_html_to_file(filename_html, html_content)
                    else:
                        print(f"Ошибка запроса: {response.status} на {pin}")
                        return None


async def save_html_to_file(file_path, html_content):
    """
    Асинхронно сохраняет HTML-контент в файл.

    :param file_path: Путь к файлу, в который будет сохранен HTML.
    :param html_content: HTML-контент для сохранения.
    """
    async with aiofiles.open(file_path, "w", encoding="utf-8") as file:
        await file.write(html_content)


asyncio.run(fetch_with_aiohttp())
