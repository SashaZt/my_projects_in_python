import csv
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
html_search_directory = current_directory / "html_search"
html_product_directory = current_directory / "html_product"
config_directory = current_directory / "config"
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)
html_product_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)

output_json_file = data_directory / "output.json"
output_xlsx_file = data_directory / "output.xlsx"
output_csv_file = data_directory / "output.csv"
log_file_path = log_directory / "log_message.log"
CONFIG_PATH = config_directory / "config.json"


BASE_URL = "https://auburnmaine.patriotproperties.com/"
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


def load_config():
    """Загрузка конфигурации из JSON-файла"""

    try:
        # Проверяем, существует ли файл конфигурации
        if not CONFIG_PATH.exists():
            logger.error(f"Ошибка: файл конфигурации не найден: {CONFIG_PATH}")
            logger.error("Создайте файл конфигурации на основе примера.")
            sys.exit(1)

        # Загружаем конфигурацию
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Проверяем наличие необходимых разделов
        required_sections = ["cookies"]
        for section in required_sections:
            if section not in config:
                logger.error(
                    f"Ошибка: в файле конфигурации отсутствует раздел '{section}'"
                )
                sys.exit(1)

        return config

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при чтении файла конфигурации: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при загрузке конфигурации: {e}")
        sys.exit(1)


def get_html():
    timeout = 60
    max_attempts = 10
    delay_seconds = 5
    # Загружаем конфигурацию после настройки логирования
    config = load_config()
    cookies = config["cookies"]
    headers = config["headers"]
    data = config["data"]
    for page in range(1, 194):
        output_html_file = html_search_directory / f"auburnmaine_0{page}.html"

        for attempt in range(max_attempts):
            try:
                if page == 1:
                    response = requests.post(
                        "https://auburnmaine.patriotproperties.com/SearchResults.asp",
                        cookies=cookies,
                        headers=headers,
                        data=data,
                        timeout=timeout,
                    )
                else:
                    params = {
                        "page": page,
                    }
                    response = requests.get(
                        "https://auburnmaine.patriotproperties.com/SearchResults.asp",
                        params=params,
                        cookies=cookies,
                        headers=headers,
                        timeout=timeout,
                    )

                # Проверка кода ответа
                if response.status_code == 200:
                    # Сохранение HTML-страницы целиком
                    with open(output_html_file, "w", encoding="utf-8") as file:
                        file.write(response.text)
                    logger.info(f"Successfully saved {output_html_file}")
                    break  # Выходим из цикла попыток при успехе
                else:
                    logger.warning(
                        f"Attempt {attempt + 1} failed for page {page} with status {response.status_code}"
                    )
                    if attempt < max_attempts - 1:  # Если не последняя попытка
                        time.sleep(delay_seconds)
                    continue

            except requests.RequestException as e:
                logger.error(
                    f"Error on attempt {attempt + 1} for page {page}: {str(e)}"
                )
                if attempt < max_attempts - 1:  # Если не последняя попытка
                    time.sleep(delay_seconds)
                continue

        else:  # Выполняется, если цикл попыток завершился без break
            logger.error(f"Failed to get page {page} after {max_attempts} attempts")


def scrap_html():
    # Extract row data
    property_data_list = []

    for html_file in html_search_directory.glob("*.html"):
        with open(html_file, "r", encoding="utf-8") as file:
            content = file.read()

        soup = BeautifulSoup(content, "lxml")
        table = soup.find("table", attrs={"id": "T1"})

        # Проверка на случай, если таблица не найдена
        if not table:
            print(f"Таблица не найдена в файле {html_file}")
            continue

        for row in table.find_all("tr", valign="top"):
            cells = row.find_all("td")

            # Skip if not enough cells
            if len(cells) < 8:  # Минимум 8 ячеек в строке с данными
                continue

            try:
                # Extract Parcel ID and Account Number from first cell
                parcel_cell = cells[0]
                parcel_link = parcel_cell.find("a")

                if not parcel_link:
                    continue  # Пропускаем строки без ссылки

                parcel_id = parcel_link.get_text(strip=True)

                # Извлекаем Account Number и URL из href
                href = parcel_link.get("href")
                # Проверяем, начинается ли href с / или нет
                url = f"{BASE_URL}{href}"

                # Извлекаем Account Number из URL
                account_match = None
                if url:
                    account_match_raw = re.search(r"AccountNumber=(\d+)", url)
                    if account_match_raw:
                        account_match = account_match_raw.group(1)

                # Location
                location_text = ""
                if len(cells) > 1:
                    location_text = cells[1].get_text(strip=True).replace("\xa0", " ")

                # Owner - может быть несколько владельцев
                owners = ""
                if len(cells) > 2:
                    owner_links = cells[2].find_all("a")
                    if owner_links:
                        owners = ";".join(a.get_text(strip=True) for a in owner_links)

                # LUC Description
                luc_links = ""
                if len(cells) > 7:
                    luc_cell = cells[7]
                    luc_links_raw = luc_cell.find_all("a")
                    if len(luc_links_raw) > 1:
                        luc_links = luc_links_raw[1].get_text(strip=True)

                property_data = {
                    "Parcel ID": parcel_id,
                    "Location": location_text,
                    "Owner": owners,
                    "LUC Description": luc_links,
                    "Account Number": account_match,
                    "URL": url,
                }
                property_data_list.append(property_data)

            except Exception as e:
                print(f"Ошибка при обработке строки в файле {html_file}: {e}")
                continue

    with open(output_json_file, "w", encoding="utf-8") as f:
        json.dump(property_data_list, f, ensure_ascii=False, indent=4)

    df = pd.DataFrame(property_data_list)
    df.to_csv(output_csv_file, index=False, encoding="utf-8")


def read_cities_from_csv():
    df = pd.read_csv(output_csv_file)
    return df["URL"].tolist()


def create_session():
    session = requests.Session()
    config = load_config()

    # Проверяем наличие заголовков в конфиге
    if "headers" in config and isinstance(config["headers"], dict):
        session.headers.update(config["headers"])

    # Проверяем наличие куки в конфиге (учитываем возможность пробела в ключе)
    cookies_key = "cookies"
    if cookies_key not in config:
        # Проверяем вариант с пробелом
        cookies_key = "cookies "

    if cookies_key in config and isinstance(config[cookies_key], dict):
        # Добавляем куки в сессию
        for cookie_name, cookie_value in config[cookies_key].items():
            session.cookies.set(cookie_name, cookie_value)

    # Инициализируем сессию, посетив главную страницу для получения дополнительных куки
    try:
        response = session.get("https://auburnmaine.patriotproperties.com/")
        if response.status_code != 200:
            logger.info(
                f"Предупреждение: статус ответа при инициализации сессии: {response.status_code}"
            )
        return session
    except Exception as e:
        logger.error(f"Ошибка при создании сессии: {e}")
        return None


def process_url(session, url, account_number):
    """
    Обрабатывает URL свойства, скачивает все доступные карточки

    Args:
        session: Объект сессии requests
        url: URL для обработки
        account_number: Номер аккаунта
        max_retries: Максимальное количество попыток (по умолчанию 10)
        retry_delay: Задержка между попытками в секундах (по умолчанию 5)

    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    config = load_config()
    MAX_RETRIES = config["MAX_RETRIES"]
    RETRY_DELAY = config["RETRY_DELAY"]
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            card_number = 1
            output_html_file = (
                html_product_directory / f"{account_number}_{card_number}.html"
            )
            if output_html_file.exists():
                return True
            # Сначала загружаем основной URL для установки нужного контекста в сессии
            main_response = session.get(url)

            if (
                "Either no search has been executed or your session has timed out"
                in main_response.text
                or main_response.status_code != 200
            ):
                logger.error(
                    f"Ошибка при загрузке основной страницы для аккаунта {account_number}"
                )
                return False

            # Теперь запрашиваем содержимое фрейма summary-bottom.asp
            bottom_url = f"{BASE_URL}/summary-bottom.asp"
            response = session.get(bottom_url)

            if (
                "Either no search has been executed or your session has timed out"
                in response.text
            ):
                logger.error(
                    f"Ошибка сессии для аккаунта {account_number}. Требуется обновление куки."
                )
                # Выбрасываем исключение вместо возврата True/False
                raise SessionExpiredException(
                    f"Сессия истекла для аккаунта {account_number}"
                )

            # Сохраняем первую страницу
            save_response(response.text, output_html_file)

            # Проверяем, сколько всего карточек
            soup = BeautifulSoup(response.text, "lxml")
            card_info = soup.select_one(
                "body > table > tbody > tr > td:nth-child(3) > p"
            )

            # Переменная для хранения общего количества карточек
            total_cards = 1  # По умолчанию предполагаем, что карточка только одна

            try:
                card_text = card_info.text.strip()

                # Получаем общее количество карточек, например, из "Card 1 of 4"
                if "of" in card_text:
                    try:
                        current_card, total_cards = map(
                            int, re.findall(r"\d+", card_text)
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при разборе информации о карточках: {e}")
                        if attempt < MAX_RETRIES:
                            logger.info(
                                f"Повторная попытка через {RETRY_DELAY} секунд..."
                            )
                            time.sleep(RETRY_DELAY)
                            continue
                        return False
                else:
                    logger.warning(
                        f"Не удалось определить количество карточек из текста: '{card_text}'"
                    )
                    return True  # Предполагаем, что это единичная карточка
            except AttributeError:
                logger.warning(
                    f"Не удалось найти информацию о карточках для аккаунта {account_number}"
                )
                return True  # Предполагаем, что это единичная карточка

            # Если только одна карточка, то уже сохранили
            if total_cards == 1:
                return True

            # Если больше одной карточки, скачиваем остальные
            all_cards_success = True
            for card_num in range(2, total_cards + 1):
                # Параметры для следующей карточки
                params = {"ValCard": "0", "Card": str(card_num)}
                card_output_html_file = (
                    html_product_directory / f"{account_number}_{card_num}.html"
                )
                if card_output_html_file.exists():
                    continue

                card_success = False
                for card_attempt in range(1, MAX_RETRIES + 1):
                    # Запрос на следующую карточку
                    logger.info(
                        f"Загрузка карточки {card_num}, попытка {card_attempt}/{MAX_RETRIES}"
                    )
                    next_response = session.get(
                        f"{BASE_URL}/Summary-bottom.asp", params=params
                    )

                    if (
                        "Either no search has been executed or your session has timed out"
                        in next_response.text
                    ):
                        logger.error(
                            f"Ошибка сессии при получении карточки {card_num} для аккаунта {account_number}"
                        )
                        if card_attempt < MAX_RETRIES:
                            # Создаем новую сессию и загружаем основной URL снова
                            session = create_session()
                            if not session:
                                logger.error("Не удалось создать новую сессию")
                                break
                            session.get(url)  # Устанавливаем контекст
                            logger.info(
                                f"Повторная попытка с новой сессией через {RETRY_DELAY} секунд..."
                            )
                            time.sleep(RETRY_DELAY)
                            continue
                        break

                    # Сохраняем карточку
                    save_response(next_response.text, card_output_html_file)
                    logger.info(
                        f"Сохранена карточка {card_num} из {total_cards} для аккаунта {account_number}"
                    )
                    card_success = True
                    break

                if not card_success:
                    all_cards_success = False
                    logger.error(
                        f"Не удалось получить карточку {card_num} для аккаунта {account_number} после {MAX_RETRIES} попыток"
                    )

            return all_cards_success

        except Exception as e:
            logger.error(
                f"Ошибка при обработке URL {url} для аккаунта {account_number}: {e}"
            )
            if attempt < MAX_RETRIES:
                logger.info(f"Повторная попытка через {RETRY_DELAY} секунд...")
                time.sleep(RETRY_DELAY)
                continue
            return False

    return False


def save_response(html_content, file_name):
    """
    Сохраняет HTML-контент в файл
    """
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(html_content)


class SessionExpiredException(Exception):
    """Исключение, которое возникает при истечении сессии"""

    pass


def process_url_list():
    """
    Обрабатывает список URL из CSV файла
    """
    session = create_session()

    if not session:
        logger.error("Не удалось создать сессию. Обработка остановлена.")
        return False

    success_count = 0
    failed_count = 0
    urls = read_cities_from_csv()
    for url in urls:
        try:
            # Извлекаем AccountNumber из URL
            account_match = re.search(r"AccountNumber=(\d+)", url)
            if not account_match:
                logger.error(f"Не удалось извлечь номер аккаунта из URL: {url}")
                failed_count += 1
                continue

            account_number = account_match.group(1)

            try:
                if process_url(session, url, account_number):
                    success_count += 1
                    logger.info(f"Успешно обработан URL для аккаунта {account_number}")
                else:
                    failed_count += 1
                    logger.error(
                        f"Не удалось обработать URL для аккаунта {account_number}"
                    )
            except SessionExpiredException as see:
                logger.critical(f"{see}. Завершение всей обработки.")
                logger.critical(
                    "Пожалуйста, обновите куки в конфигурационном файле и перезапустите скрипт."
                )
                return False  # Прерываем всю обработку при ошибке сессии

        except Exception as e:
            failed_count += 1
            logger.error(f"Ошибка при обработке URL {url}: {e}")

    logger.info(
        f"Обработка завершена. Успешно: {success_count}, Ошибок: {failed_count}"
    )
    return success_count > 0


if __name__ == "__main__":
    # get_html()
    # scrap_html()
    # Загружаем список URL из CSV файла

    # Обрабатываем список URL
    process_url_list()
