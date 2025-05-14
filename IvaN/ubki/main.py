# Рабочий код для сбора данных с сайта https://edrpou.ubki.ua/ua
import concurrent.futures
import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from loguru import logger

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_directory = current_directory / "html"
log_directory = current_directory / "log"
json_directory = current_directory / "json"
# Пути к файлам
output_csv_file = current_directory / "urls.csv"
# Создание директорий, если их нет
log_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def get_json(dr_common_data):

    headers = {
        "accept": "*/*",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://edrpou.ubki.ua",
        "priority": "u=1, i",
        "referer": "https://edrpou.ubki.ua/ua?dr_common_data=13498562",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "x-csrf-token": "WpavMfeCR5hfcJhzqZdq43BJObkLaJLDTdOG4FodKjBo7-1ive0R3BdH2RLn7i2TCgBz0FI_3aAunuq0BXcYVQ==",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": "_ga=GA1.1.1041931148.1741212566; device-referrer=; _csrf=6c1bc4a29faf4f5a1141fd9929a8de249272ed447723fb08e1a64b768e4f34fba%3A2%3A%7Bi%3A0%3Bs%3A5%3A%22_csrf%22%3Bi%3A1%3Bs%3A32%3A%222yBSJoVDH7AaNyGpzIJiYWOccMlT_j2e%22%3B%7D; device-source=https://edrpou.ubki.ua/ua/36422974; LNG=UA; _ga_3YCXQ6T6Q8=GS2.1.s1747207929$o4$g1$t1747208023$j0$l0$h0; _ga_F6HFCJ1TNT=GS2.1.s1747207929$o4$g1$t1747208023$j0$l0$h0; LNG=UA",
    }
    url = f"https://edrpou.ubki.ua/srchopenitems?dr_common_data={dr_common_data}&signature=6f532b24fde73cb4aaaf4cc9c5c35aa0414d68ee&scheme=cki&reqid="
    payload = f"tp=1&page=1&dr_common_data={dr_common_data}&dr_regions=&dr_edrstate=&dr_kvedcode=&dr_search_just=false&dr_search_type=1"

    json_files = json_directory / f"{dr_common_data}.json"

    if json_files.exists():
        logger.info(f"В наличии {json_files}")
        with open(json_files, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        return json_data["clients"][0]["taxNumber"]

    response = requests.post(
        url,
        data=payload,
        headers=headers,
        timeout=30,
    )
    if response.status_code == 200:
        json_data = response.json()

        if json_data.get("clients") and len(json_data["clients"]) > 0:
            try:
                client = json_data["clients"][0]["taxNumber"]
                with open(json_files, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
                logger.info(json_files)
                return client
            except KeyError:
                logger.error(f"Ошибка: нет ключа 'taxNumber' для {dr_common_data}")
        else:
            logger.error(f"Нет клиентов для {dr_common_data}")
        return None
    else:
        logger.error(f"{response.status_code} для {dr_common_data}")
    return None  # Возвращаем None, если ни один запрос не был успешным


def get_html(taxNumber):
    if taxNumber is None:
        logger.error("Не удалось получить номер налогоплательщика.")
        return
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "Cookie": "LNG=UA; _ga=GA1.1.1041931148.1741212566; device-referrer=; _csrf=6c1bc4a29faf4f5a1141fd9929a8de249272ed447723fb08e1a64b768e4f34fba%3A2%3A%7Bi%3A0%3Bs%3A5%3A%22_csrf%22%3Bi%3A1%3Bs%3A32%3A%222yBSJoVDH7AaNyGpzIJiYWOccMlT_j2e%22%3B%7D; _ga_3YCXQ6T6Q8=GS2.1.s1747207929$o4$g0$t1747207929$j0$l0$h0; _ga_F6HFCJ1TNT=GS2.1.s1747207929$o4$g0$t1747207929$j0$l0$h0; device-source=https://edrpou.ubki.ua/ua/36422974; LNG=UA",
    }
    html_files = html_directory / f"{taxNumber}.html"

    if html_files.exists():
        return

    response = requests.get(
        f"https://edrpou.ubki.ua/ua/{taxNumber}",
        headers=headers,
        timeout=30,
    )
    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open(html_files, "w", encoding="utf-8") as file:
            file.write(response.text)
        logger.info(html_files)


def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


def main():
    urls = read_cities_from_csv(output_csv_file)  # Берём все URL

    # Здесь укажите количество потоков, которое вы хотите использовать
    num_threads = 20  # Например, 5 потоков

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Создаем список задач для get_json
        future_to_url = {executor.submit(get_json, url): url for url in urls}

        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                taxNumber = future.result()
                if taxNumber is not None:
                    # Вызываем get_html для полученного taxNumber
                    executor.submit(get_html, taxNumber)
                else:
                    logger.error(
                        f"Не удалось получить номер налогоплательщика для {url}."
                    )
            except Exception as e:
                logger.error(f"Произошла ошибка при обработке {url}: {e}")


if __name__ == "__main__":
    while True:
        logger.info("Запуск обработки...")
        main()
        logger.info("Обработка завершена. Ожидание 300 секунд...")
        time.sleep(300)  # Пауза на 5 минут (300 секунд)
