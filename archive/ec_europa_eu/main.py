from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from selectolax.parser import HTMLParser
import random
import pandas as pd
from configuration.logger_setup import logger

url = "https://ec.europa.eu/taxation_customs/dds2/eos/eori_detail.jsp"
cookies = {
    "JSESSIONID": "RJWEVdYmoJZhsxkgNsUaMVqTQnnKqqdZvoIqpj9_YxlQBvvMHBx3!-1265498900",
}

headers = {
    "Accept": "*/*",
    "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "Connection": "keep-alive",
    "DNT": "1",
    "Referer": "https://ec.europa.eu/taxation_customs/dds2/eos/eori_validation.jsp?Lang=en&EoriNumb=PL39000000014140Z&Expand=true",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


def load_proxies():
    file_path = "1000 ip.txt"
    # Загрузка списка прокси из файла
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


def read_txt_file():
    # Определяем путь к файлу pl.txt в текущей директории
    pl_file_path = Path.cwd() / "ltua.txt"

    # Читаем файл и возвращаем список строк
    with pl_file_path.open("r") as file:
        lines = file.read().splitlines()  # splitlines() удаляет символы переноса строк

    return lines


def fetch_url_data(eori_number, cookies, headers, proxies, max_attempts=10):
    params = {
        "Lang": "en",
        "EoriNumb": eori_number,
    }

    for attempt in range(max_attempts):
        try:
            # Выбираем случайное прокси для каждого запроса
            proxy = random.choice(proxies)
            proxies_dict = {"http": proxy, "https": proxy}

            response = requests.get(
                url,
                params=params,
                cookies=cookies,
                headers=headers,
                proxies=proxies_dict,
            )
            response.raise_for_status()  # Проверяем, был ли успешный запрос
            return (
                response.text,
                None,
            )  # Возвращаем содержимое ответа и None, если все в порядке

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Attempt {attempt + 1}/{max_attempts} failed for EORI {eori_number} with proxy {proxy}: {str(e)}"
            )

            # Если это была последняя попытка, возвращаем ошибку
            if attempt == max_attempts - 1:
                return None, (
                    f"Error: {response.status_code}"
                    if response
                    else "Error: No Response"
                )

            # Иначе продолжаем с новым прокси
            continue

    # На случай, если что-то пошло не так и цикл завершился
    return None, "Error: Max attempts exceeded without success"


def parse_table(html, eori_number):
    tree = HTMLParser(html)
    table_data = {}

    # Предопределенные ключи, которые должны присутствовать в результате
    keys = [
        "EORI Number",
        "Request date",
        "EORI Name",
        "Address name",
        "Street number",
        "Postal code",
        "City",
        "Country name",
        "Validity",
    ]

    # Инициализируем table_data с None для каждого ключа
    for key in keys:
        table_data[key] = None

    # Найдем все строки таблицы
    rows = tree.css("tbody.ecl-table__body tr.ecl-table__row")

    # Проверка на валидность номера
    validity = "Неизвестный статус"  # По умолчанию статус неизвестен

    for row in rows:
        # Найдем все ячейки в строке
        cells = row.css("td.ecl-table__cell")

        if len(cells) >= 2:  # Убедимся, что в строке есть хотя бы две ячейки
            key = cells[0].text().strip()
            value = cells[1].text().strip()
            if key in table_data:
                table_data[key] = value
            validity = "Номер валидный"
        elif "This EORI number is not valid." in row.text():
            validity = "Номер не валидный"

    # Добавляем результат проверки на валидность и EORI Number в table_data
    table_data["Validity"] = validity
    table_data["EORI Number"] = eori_number  # Записываем переданный EORI Number

    return table_data


def append_to_csv(row, output_file):
    # Проверяем, существует ли файл и содержит ли он данные
    file_exists = Path(output_file).exists() and Path(output_file).stat().st_size > 0

    # Создаем DataFrame для строки
    df = pd.DataFrame([row])

    # Открываем файл в режиме добавления и записываем строку
    with open(output_file, "a", encoding="utf-8", newline="") as f:
        df.to_csv(f, header=not file_exists, index=False, sep=";")


def process_urls_in_threads(output_file="results.csv", num_threads=10):
    proxies = load_proxies()  # Загружаем список всех прокси
    eori_numbers = read_txt_file()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_url = {
            executor.submit(
                fetch_url_data, eori_number, cookies, headers, proxies
            ): eori_number
            for eori_number in eori_numbers
        }

        for future in as_completed(future_to_url):
            eori_number = future_to_url[future]
            logger.info(eori_number)
            try:
                src, error = future.result()

                if src is None:  # Если был возврат ошибки
                    # Создаем запись с ошибкой

                    row = {
                        "EORI Number": eori_number,
                        "Request date": None,
                        "EORI Name": None,
                        "Address name": None,
                        "Street number": None,
                        "Postal code": None,
                        "City": None,
                        "Country name": None,
                        "Validity": error,
                    }
                else:
                    parsed_data = parse_table(src, eori_number)

                    # Подготавливаем данные для записи
                    row = {"EORI Number": eori_number}
                    row.update(parsed_data)

                # Используем отдельную функцию для записи в CSV
                append_to_csv(row, output_file)

            except Exception as exc:
                logger.error(f"EORI {eori_number} generated an exception: {exc}")

    logger.info(f"Выполнено {output_file}")


if __name__ == "__main__":
    process_urls_in_threads()
