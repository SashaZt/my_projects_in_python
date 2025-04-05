import asyncio
import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from logger import logger
from playwright.async_api import async_playwright

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
output_html_file = html_directory / "leroymerlin.html"


def get_html():

    cookies = {
        "auto-contextualization_attempt": "true",
        "pa_privacy": "%22exempt%22",
        "_pcid": "%7B%22browserId%22%3A%22m92o0q4hag9yp49x%22%2C%22_t%22%3A%22mor2y7gv%7Cm92o0q4w%22%7D",
        "_pctx": "%7Bu%7DN4IgrgzgpgThIC4B2YA2qA05owMoBcBDfSREQpAeyRCwgEt8oBJAE0RXSwH18yBbSjABMATwDsAcwAeAH34BOYZQAMARwAs0kAF8gA",
        "search_session": "98d4bc9d-ec38-4964-9d87-e5580a2c2932|28558dab-c963-4d0a-8484-8fa043e4de36",
        "lm-csrf": "NRwFebxOetyJxoWRgDdTrtL/RC6V22G4PHMpt6vAIqQ=.1743788028610.gf9zZQ4PaLxS3inL/MkaEqmqxUHy2pY9KI3nnJJ1piA=",
        "datadome": "HMpjtGnjVp~W11i2li6SPskEeV~K01mTy8LnBXo8JPT22zvgyfZeiNSXvm0NE~Vus7mZyGhYrJQFHEmOCf1b3rvPpqyU2nXqTmzNlqfeqMo1iesS9wYTuJlIWO9xqwAV",
        "_dd_s": "rum=0&expire=1743788936024",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://www.leroymerlin.pl/produkty/odkurzacz-przemyslowy-starmix-basic-ipulse-l-1635-35-l-1600w-80900005.html",
        cookies=cookies,
        headers=headers,
        timeout=10,
    )

    # Проверка кода ответа
    if response.status_code == 200:

        # Сохранение HTML-страницы целиком
        with open(output_html_file, "w", encoding="utf-8") as file:
            file.write(response.text)
        logger.info(f"Successfully saved {output_html_file}")
    else:
        logger.error(f"Failed to get HTML. Status code: {response.status_code}")


def remove_at_type(data):
    """Рекурсивно удаляет ключи '@type' из словаря."""
    if isinstance(data, dict):
        # Создаем новый словарь без '@type'
        new_data = {k: remove_at_type(v) for k, v in data.items() if k != "@type"}
        return new_data
    elif isinstance(data, list):
        return [remove_at_type(item) for item in data]
    return data


def scrap_html():
    with open(output_html_file, "r", encoding="utf-8") as file:
        content = file.read()
    soup = BeautifulSoup(content, "lxml")

    # Извлечение данных из JSON-скриптов
    result = {}
    for script in soup.find_all(
        "script", {"type": "application/json", "class": "dataJsonLd"}
    ):
        json_data = json.loads(script.string)
        result.update(json_data)

    # Извлечение характеристик из таблицы
    features = {}
    table = soup.find("table", {"class": "o-product-features"})
    if table:
        for row in table.find_all("tr", {"class": "m-product-attr-row"}):
            name = row.find("th", {"class": "m-product-attr-row__name"}).text.strip()
            value = row.find("td", {"class": "m-product-attr-row__value"}).text.strip()
            # Преобразование чисел, если возможно
            try:
                value = float(value) if "." in value else int(value)
            except ValueError:
                pass
            features[name] = value

    # Добавление характеристик в результат
    if features:
        result["specifications"] = features

    # Удаление всех '@type'
    result = remove_at_type(result)

    # Сохранение в файл
    with open("product.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    return result


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
    scrap_html()
    # main_realoem()
    # get_html()
    # asyncio.run(main())
