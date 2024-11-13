import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

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


def get_cookies():
    """Извлекает заголовки и cookies из файла конфигурации.

    Функция читает конфигурационный файл, содержащий строку cURL, и извлекает из неё
    значения заголовков и cookies для последующего использования в HTTP-запросах.

    Returns:
        tuple: Кортеж, содержащий два словаря - headers и cookies, которые могут
        быть переданы в запросы для авторизации и других настроек.
    """
    with open(config_txt_file, "r", encoding="utf-8") as f:
        curl_text = f.read()

    # Инициализация словарей для заголовков и кук
    headers = {}
    cookies = {}

    # Извлечение всех заголовков из параметров `-H`
    header_matches = re.findall(r"-H '([^:]+):\s?([^']+)'", curl_text)
    for header, value in header_matches:
        if header.lower() == "cookie":
            # Обработка куки отдельно, разделяя их по `;`
            cookies = {
                k.strip(): v
                for pair in value.split("; ")
                if "=" in pair
                for k, v in [pair.split("=", 1)]
            }
        else:
            headers[header] = value

    return headers, cookies


def get_start_page():
    file_path = Path("page.html")
    headers, cookies = get_cookies()
    response = requests.get('https://as-pl.com/ru',
                            cookies=cookies, headers=headers)
    if response.status_code == 200 and "text/html" in response.headers.get("Content-Type", ""):
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


if __name__ == "__main__":
    # get_start_page()
    extract_links()
