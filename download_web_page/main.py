import csv
import json
import random
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)


def get_html():

    cookies = {
        "cf_clearance": "rwx6YbwNlQnQsXFJNnLMDf3.oCX7P7sbHhXMP7BNEA8-1742659575-1.2.1.1-_BzzCS.mf4jeT1_fZCEoRx1FogQXKbjDkCPCzKvLs1Qr5fG8WXs5eiONAhh5Tsynt15cGDWRMJyJ9MbJQ_L8fUFISKSrlDa05rr3KtqpSbIqpNlyIhk1kBNGrAOuRQ_hCHxD708qQTj9r0Jt5yzGwOpQ2e9i4rcRBamyQKVQ.YALbi.UORxCpZDs57XPnD5xVOXqdSRWmDiG.2JRudc1fFiOzHVesBO4Er3K_LfolUTVrB6In_giAu4sdIJcTmNJygye048a5PJ9GCfFWpKpKHa2zwUidU0eqP0ifL9Ko9R2bJQQSu_ppK93aoBVcDsIFCmFKKcOw5AVAW3iQVGzQx_gBmi6u_c1QLqreEZW6ts",
        "XSRF-TOKEN": "eyJpdiI6ImJSblNWU3BHNks0THNxd3NVbHhhVVE9PSIsInZhbHVlIjoiTmdzN2hpa1hpeDFsbnFCZHk4Rk8xc0NPY1pzRms0ajZqMDBBV3I2Y1NReUFjRXlaRFU3SWE3RFNya2QyaGN6RytNbDBWYkkvVkxvVDQ4cTNQM0JiMjFsdVh1M20yU3RuczdYa0FpKzQvRHVIK05xL3JTTjR0d2dFU2lqbmlOZnEiLCJtYWMiOiIxMWJmMTNmNzQyMTMxYTEwMTcyMTEwMjhjMWViZDIyZDhjYTZmODhjNjVhM2ZmZDQ3NTM5NzU2YzhkZmRhZDY4IiwidGFnIjoiIn0%3D",
        "tikleap_session": "eyJpdiI6InpSMm9mbE9FemxjUGk1emRwMFZ6Y3c9PSIsInZhbHVlIjoiVUpDTUkvK1cwRmNBaGtqNmdIaHNRc2pOTWI4dXRJWjNCTUcxU21oclJYQ0c2TTJiOXo3eVJ6RFlscGN6ekt1eWNNUTZrUTJwVWVJZVVuRU9vcldlNllXRmMvVEZkRnFRVWFRNkQzc2k0dTdLajIrMDF4QzczcXFRVURMSTVZeEIiLCJtYWMiOiIxZTRiZWIzOTUyYzA0NGFjYjM5MzExZmExZmI0OTg0YTdhMzA4ZGU3NThkMWFmZjdkYTQ0MTJjZWJjZmYzMTk5IiwidGFnIjoiIn0%3D",
    }

    headers = {
        "accept": "*/*",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "dnt": "1",
        "priority": "u=1, i",
        "referer": "https://www.tikleap.com/",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
        # 'cookie': 'cf_clearance=rwx6YbwNlQnQsXFJNnLMDf3.oCX7P7sbHhXMP7BNEA8-1742659575-1.2.1.1-_BzzCS.mf4jeT1_fZCEoRx1FogQXKbjDkCPCzKvLs1Qr5fG8WXs5eiONAhh5Tsynt15cGDWRMJyJ9MbJQ_L8fUFISKSrlDa05rr3KtqpSbIqpNlyIhk1kBNGrAOuRQ_hCHxD708qQTj9r0Jt5yzGwOpQ2e9i4rcRBamyQKVQ.YALbi.UORxCpZDs57XPnD5xVOXqdSRWmDiG.2JRudc1fFiOzHVesBO4Er3K_LfolUTVrB6In_giAu4sdIJcTmNJygye048a5PJ9GCfFWpKpKHa2zwUidU0eqP0ifL9Ko9R2bJQQSu_ppK93aoBVcDsIFCmFKKcOw5AVAW3iQVGzQx_gBmi6u_c1QLqreEZW6ts; XSRF-TOKEN=eyJpdiI6ImJSblNWU3BHNks0THNxd3NVbHhhVVE9PSIsInZhbHVlIjoiTmdzN2hpa1hpeDFsbnFCZHk4Rk8xc0NPY1pzRms0ajZqMDBBV3I2Y1NReUFjRXlaRFU3SWE3RFNya2QyaGN6RytNbDBWYkkvVkxvVDQ4cTNQM0JiMjFsdVh1M20yU3RuczdYa0FpKzQvRHVIK05xL3JTTjR0d2dFU2lqbmlOZnEiLCJtYWMiOiIxMWJmMTNmNzQyMTMxYTEwMTcyMTEwMjhjMWViZDIyZDhjYTZmODhjNjVhM2ZmZDQ3NTM5NzU2YzhkZmRhZDY4IiwidGFnIjoiIn0%3D; tikleap_session=eyJpdiI6InpSMm9mbE9FemxjUGk1emRwMFZ6Y3c9PSIsInZhbHVlIjoiVUpDTUkvK1cwRmNBaGtqNmdIaHNRc2pOTWI4dXRJWjNCTUcxU21oclJYQ0c2TTJiOXo3eVJ6RFlscGN6ekt1eWNNUTZrUTJwVWVJZVVuRU9vcldlNllXRmMvVEZkRnFRVWFRNkQzc2k0dTdLajIrMDF4QzczcXFRVURMSTVZeEIiLCJtYWMiOiIxZTRiZWIzOTUyYzA0NGFjYjM5MzExZmExZmI0OTg0YTdhMzA4ZGU3NThkMWFmZjdkYTQ0MTJjZWJjZmYzMTk5IiwidGFnIjoiIn0%3D',
    }

    response = requests.get(
        "https://www.tikleap.com/", cookies=cookies, headers=headers
    )

    # Проверка кода ответа
    if response.status_code == 200:
        output_html_file = html_directory / "tikleap.html"
        # Сохранение HTML-страницы целиком
        with open(output_html_file, "w", encoding="utf-8") as file:
            file.write(response.text)
        logger.info(f"Successfully saved {output_html_file}")
    else:
        logger.error(f"Failed to get HTML. Status code: {response.status_code}")


def scrap_html():
    with open("freepik.html", "r", encoding="utf-8") as file:
        content = file.read()
    soup = BeautifulSoup(content, "lxml")
    # Находим все элементы <figure> с классом "$relative"
    figures = soup.find_all("figure", class_="$relative")

    # Список для хранения результатов
    results = []

    # Проходим по всем найденным <figure>
    for figure in figures:
        # Ищем <img> внутри каждого <figure>
        img = figure.find("img")
        if img:
            # Извлекаем атрибуты alt и src
            alt_text = img.get("alt", "")  # Если alt отсутствует, вернем пустую строку
            src_url = img.get("src", "")  # Если src отсутствует, вернем пустую строку
            results.append({"alt": alt_text, "src": src_url})

    # Выводим результаты
    for result in results:
        print(f"Alt: {result['alt']}")
        print(f"Src: {result['src']}")
        print("---")

    # Если нужно сохранить в список словарей или файл, вот пример:
    import json

    with open("image_data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)


import asyncio

from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=False
        )  # Set headless=True in production

        # Create new context with optimizations
        context = await browser.new_context(
            bypass_csp=True,
            java_script_enabled=True,
            permissions=["geolocation"],
            device_scale_factor=1.0,
            has_touch=True,
            ignore_https_errors=True,
        )

        # Disable loading of images, fonts and other media files
        await context.route(
            "**/*",
            lambda route, request: (
                route.abort()
                if request.resource_type in ["image", "media", "font", "stylesheet"]
                else route.continue_()
            ),
        )

        # Create new page
        page = await context.new_page()

        # Navigate to the website (replace with your target URL)
        await page.goto("https://www.tikleap.com/")  # Replace with your actual URL
        await asyncio.sleep(50)

        # Wait for the postal code element to appear and click it
        postal_code_button = await page.wait_for_selector(
            'span:text("Wpisz kod pocztowy")'
        )
        await postal_code_button.click()

        # Wait for the input field to appear
        postal_code_input = await page.wait_for_selector(
            'input[aria-describedby="hnf-postalcode-helper"]'
        )

        # Type the postal code
        await postal_code_input.fill("22-100")

        # Press Enter
        await postal_code_input.press("Enter")

        # Wait a moment to see the result (adjust as needed)
        await asyncio.sleep(5)

        # Close browser
        await browser.close()


if __name__ == "__main__":
    # scrap_html()
    # main_realoem()
    # get_htmls()
    # get_html()
    asyncio.run(main())
