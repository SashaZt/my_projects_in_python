import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

# Ваши модули

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
img_files_directory = current_directory / "img_files"
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"

# Создание директорий, если их нет
html_files_directory.mkdir(parents=True, exist_ok=True)
img_files_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

# Пути к файлам
output_csv_file = data_directory / "output.csv"
xlsx_result = data_directory / "result.xlsx"
json_result = data_directory / "result.json"
file_proxy = configuration_directory / "proxy.txt"
config_txt_file = configuration_directory / "config.txt"




def get_start_page():
    file_path = Path("page.html")
    headers, cookies = get_cookies()
    response = requests.get("https://as-pl.com/ru", cookies=cookies, headers=headers)
    if response.status_code == 200 and "text/html" in response.headers.get(
        "Content-Type", ""
    ):
        file_path.write_text(response.text, encoding="utf-8")


def extract_links():

    # Список ссылок, которые нужно исключить
    exclude_links = [
        "https://as-pl.com/ru/c/others_parts_op",
        "https://as-pl.com/ru/c/washers_nuts_screws",
        "https://as-pl.com/ru/c/nox_sensor_260288",
        "https://as-pl.com/ru/c/machines_and_parts_MM",
    ]
    file_path = Path("page.html")
    if not file_path.exists():
        print("HTML file not found. Please run get_start_page() first.")
        return

    # Чтение HTML и парсинг
    html_content = file_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, "lxml")

    # Поиск селектора #top-categories-container > div и сбор href
    links = set()
    for div in soup.select("#top-categories-container > div a[href]"):
        href = div.get("href")
        full_url = f"https://as-pl.com{href}"
        if full_url not in exclude_links:
            links.add(full_url)

    # Запись ссылок в CSV
    df = pd.DataFrame(list(links), columns=["url"])
    df.to_csv(output_csv_file, index=False, encoding="utf-8")
    print(f"Extracted links saved to {output_csv_file}")


def get_category():
    import requests

    cookies = {
        "AS_COOKIE_ALLOW": "1",
        "session": "89p3h63buiiodnim295gapsi45",
        "route": "1732107681.185.132827.203180|4ea7291f9f635e972563a972b641033c",
    }

    headers = {
        "accept": "*/*",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "content-type": "multipart/form-data; boundary=----WebKitFormBoundary9RMkIHAtUw0TYZAl",
        # 'cookie': 'AS_COOKIE_ALLOW=1; session=89p3h63buiiodnim295gapsi45; route=1732107681.185.132827.203180|4ea7291f9f635e972563a972b641033c',
        "dnt": "1",
        "origin": "https://as-pl.com",
        "priority": "u=1, i",
        "referer": "https://as-pl.com/ru/c/starter_screws_for_solenoids_6335",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }

    # data = '------WebKitFormBoundary9RMkIHAtUw0TYZAl--\r\n'

    response = requests.post(
        "https://as-pl.com/ru/c/starter_screws_for_solenoids_6335/_/1",
        cookies=cookies,
        headers=headers,
        # data=data,
    )
    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open("proba_1.html", "w", encoding="utf-8") as file:
            file.write(response.text)
    logger.info(response.status_code)


if __name__ == "__main__":
    # get_start_page()
    # extract_links()
    get_category()
