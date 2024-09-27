import requests
from configuration.logger_setup import logger
from bs4 import BeautifulSoup
from tqdm import tqdm
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd
import requests
import random
import csv


# Установка директорий для логов и данных
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
data_directory = current_directory / "data"

html_files_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

output_csv_file = data_directory / "output.csv"
csv_file_successful = data_directory / "identifier_successful.csv"


cookies = {
    "PHPSESSID": "c95e174e4800458653c20b9dc207596e",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    # 'cookie': 'PHPSESSID=c95e174e4800458653c20b9dc207596e',
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "referer": "https://clarity-project.info/edr/37542726",
    "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
}


def load_proxies():
    file_path = "roman.txt"
    # Загрузка списка прокси из файла
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


# Функция для запроса и сохранения HTML
def fetch_and_save_html(identifier, successful_urls, proxies):
    if identifier in successful_urls:
        logger.info(f"| Компания уже была обработана, пропускаем. |")
        return

    try:
        proxy = random.choice(proxies)  # Выбираем случайный прокси
        proxies_dict = {"http": proxy, "https": proxy}

        base_url = "https://clarity-project.info/edr"
        url = f"{base_url}/{identifier}/finances"

        # Отправляем запрос
        response = requests.get(
            url,
            proxies=proxies_dict,
            headers=headers,
            cookies=cookies,
        )

        # Проверяем статус ответа
        if response.status_code == 200:
            # Формируем путь для сохранения файла
            file_path = html_files_directory / f"{identifier}.html"
            # Сохраняем HTML в файл
            file_path.write_text(response.text, encoding="utf-8")
            successful_urls.add(identifier)
            write_to_csv(identifier, csv_file_successful)

        else:
            logger.error(
                f"Ошибка: не удалось получить данные для {identifier}. Статус: {response.status_code}"
            )

    except Exception as e:
        logger.error(f"Произошла ошибка при обработке {identifier}: {e}")


# Функция для чтения файла и запуска многопоточности
def process_infox_file(max_workers):
    proxies = load_proxies()  # Загружаем список всех прокси

    successful_urls = get_successful_urls(csv_file_successful)
    urls_df = pd.read_csv(output_csv_file)

    # Создаем прогресс-бар
    total_urls = len(urls_df)
    progress_bar = tqdm(
        total=total_urls,
        desc="Обработка файлов",
        bar_format="{l_bar}{bar} | Время: {elapsed} | Осталось: {remaining} | Скорость: {rate_fmt}",
    )

    # Запускаем многопоточность
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(fetch_and_save_html, url, successful_urls, proxies)
            for url in urls_df["identifier"]
        ]

        for future in as_completed(futures):
            try:
                future.result()  # Получаем результат выполнения задачи
            except Exception as e:
                logger.error(f"Error occurred: {e}")
            finally:
                # Обновляем прогресс-бар по завершении каждой задачи
                progress_bar.update(1)

    # Закрываем прогресс-бар
    progress_bar.close()
    logger.info("Все запросы выполнены.")


def write_to_csv(data, filename):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{data}\n")


# Функция для парсинга одного HTML файла
def parse_html_file(file_path):
    with open(file_path, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")

    # Список кодов
    codes = [
        "1012",
        "1195",
        "1495",
        "1595",
        "1621",
        "1695",
        "1900",
        "2350",
        "2000",
        "2280",
        "2285",
        "2505",
        "2510",
    ]

    # Получаем заголовок страницы
    page_title = None
    page_title_label = soup.select_one(
        "body > div.entity-page-wrap > div.entity-content-wrap > div.entity-header.px-10 > div:nth-child(3) > a"
    )
    if page_title_label:
        page_title = page_title_label.text.replace("#", "")

    # Ищем количество работников
    number_of_employees = None
    employee_label = soup.find("td", string="Кількість працівників")
    if employee_label:
        number_of_employees = employee_label.find_next_sibling("td").string.strip()

    # Ищем КАТОТТГ
    katottg = None
    katottg_label = soup.find("td", string="КАТОТТГ")
    if katottg_label:
        katottg = katottg_label.find_next_sibling("td").string.strip()

    # Словарь для текущей единицы данных
    results = {
        "page_title": page_title,
        "number_of_employees": number_of_employees,
        "katottg": katottg,
    }
    nobr_start = None
    nobr_end = None

    nobr_start_el = soup.select_one(
        "body > div.entity-page-wrap > div.entity-content-wrap > div.entity-content > table:nth-child(6) > thead > tr > th:nth-child(3) > span"
    )
    if nobr_start_el:
        nobr_start = nobr_start_el.text.strip()

    nobr_end_el = soup.select_one(
        "body > div.entity-page-wrap > div.entity-content-wrap > div.entity-content > table:nth-child(6) > thead > tr > th:nth-child(4) > span"
    )
    if nobr_end_el:
        nobr_end = nobr_end_el.text.strip()

    # Проходим по каждой строке таблицы и извлекаем значения для кодов
    for row in soup.select("tbody tr"):
        code_cell = row.select_one("td:nth-child(2)")

        if code_cell:
            code = code_cell.text.strip()
            if code in codes:
                # Извлекаем значения для начала и конца года
                beginning_of_year = row.select_one("td:nth-child(3)")
                end_of_year = row.select_one("td:nth-child(4)")

                # Сохраняем значения в словарь, если они существуют, иначе - None
                results[f"beginning_of_the_year_{code}"] = (
                    f"{beginning_of_year.text.strip()}{nobr_start}"
                    if beginning_of_year
                    else None
                )
                results[f"end_of_the_year_{code}"] = (
                    f"{end_of_year.text.strip()}{nobr_end}" if end_of_year else None
                )

    return results


# Основная функция для чтения всех файлов и записи в Excel с использованием многопоточности
def parse_all_files_and_save_to_excel(max_threads):
    # Список для хранения всех единиц данных
    all_results = []

    # Получаем все файлы в директории
    files = list(html_files_directory.glob("*.html"))

    progress_bar = tqdm(
        total=len(files),
        desc="Обработка файлов",
        bar_format="{l_bar}{bar} | Время: {elapsed} | Осталось: {remaining} | Скорость: {rate_fmt}",
    )

    lock = Lock()  # Для безопасного обновления прогресс-бара из разных потоков

    # Функция для обработки файлов в многопоточном режиме
    def process_file(file):
        result = parse_html_file(file)

        # Обновляем прогресс-бар
        with lock:
            progress_bar.update(1)

        return result

    # Используем ThreadPoolExecutor для многопоточного выполнения
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        # Передаем список файлов для обработки в пул потоков
        results = list(executor.map(process_file, files))
        all_results.extend(results)

    # Закрываем прогресс-бар
    progress_bar.close()

    # Запись всех данных в Excel через pandas
    df = pd.DataFrame(all_results)
    df.to_excel("financial_data.xlsx", index=False, engine="openpyxl")
    logger.info(f"Данные успешно записаны в 'financial_data.xlsx'")


def get_successful_urls(csv_file_successful):
    """Читает успешные URL из CSV-файла и возвращает их в виде множества."""
    if not Path(csv_file_successful).exists():
        return set()

    with open(csv_file_successful, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        successful_urls = {row[0] for row in reader if row}
    return successful_urls


# Пример использования


def parsing():
    with open("proba.html", encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")

    # Список кодов
    codes = [
        "1012",
        "1195",
        "1495",
        "1595",
        "1621",
        "1695",
        "1900",
        "2350",
        "2000",
        "2280",
        "2285",
        "2505",
        "2510",
    ]

    # Список для хранения всех единиц данных
    all_results = []

    # Получаем заголовок страницы
    page_title = soup.select_one(
        "body > div.entity-page-wrap > div.entity-content-wrap > div.entity-header.px-10 > div:nth-child(3) > a"
    ).text.replace("#", "")

    # Ищем количество работников
    number_of_employees = None
    employee_label = soup.find("td", string="Кількість працівників")
    if employee_label:
        number_of_employees = employee_label.find_next_sibling("td").string.strip()

    # Ищем КАТОТТГ
    katottg = None
    katottg_label = soup.find("td", string="КАТОТТГ")
    if katottg_label:
        katottg = katottg_label.find_next_sibling("td").string.strip()

    # Словарь для текущей единицы данных
    results = {
        "page_title": page_title,
        "number_of_employees": number_of_employees,
        "katottg": katottg,
    }

    # Проходим по каждой строке таблицы
    for row in soup.select("tbody tr"):
        # Извлекаем код строки (находится во втором столбце)
        code_cell = row.select_one("td:nth-child(2)")

        if code_cell and code_cell.text.strip() in codes:
            code = code_cell.text.strip()

            # Извлекаем значения для начала и конца года
            beginning_of_year = row.select_one("td:nth-child(3)").text.strip()
            end_of_year = row.select_one("td:nth-child(4)").text.strip()

            # Сохраняем значения в словарь
            results[f"beginning_of_the_year_{code}"] = beginning_of_year
            results[f"end_of_the_year_{code}"] = end_of_year

    # Добавляем словарь в список all_results
    all_results.append(results)

    # Выводим список словарей
    print(all_results)

    # Пример записи в Excel через pandas
    df = pd.DataFrame(all_results)
    df.to_excel("financial_data.xlsx", index=False, engine="openpyxl")


# def remove_successful_urls():
#     # Проверяем, если файл с успешными URL пустой
#     if csv_file_successful.stat().st_size == 0:
#         logger.info("Файл urls_successful.csv пуст, ничего не делаем.")
#         return

#     # Загружаем данные из обоих CSV файлов
#     try:
#         # Читаем csv_url_products с заголовком
#         df_products = pd.read_csv(output_csv_file)

#         # Читаем csv_file_successful без заголовка и присваиваем имя столбцу
#         df_successful = pd.read_csv(
#             csv_file_successful, header=None, names=["identifier"]
#         )
#     except FileNotFoundError as e:
#         logger.error(f"Ошибка: {e}")
#         return

#     # Проверка на наличие столбца 'url' в df_products
#     if "url" not in df_products.columns:
#         logger.info("Файл url_products.csv не содержит колонку 'identifier'.")
#         return

#     # Удаляем успешные URL из списка продуктов
#     initial_count = len(df_products)
#     df_products = df_products[~df_products["identifier"].isin(df_successful["url"])]
#     final_count = len(df_products)

#     # Если были удалены какие-то записи
#     if initial_count != final_count:
#         # Перезаписываем файл csv_url_products
#         df_products.to_csv(output_csv_file, index=False)
#         # Очищаем файл csv_file_successful
#         open(csv_file_successful, "w").close()
#         logger.info(f"Файл {csv_file_successful.name} очищен.")
#     else:
#         print("Не было найдено совпадающих URL для удаления.")


if __name__ == "__main__":
    # Указываем путь к файлу infox.txt
    # remove_successful_urls()
    # Базовый URL
    # Замените на реальный URL
    max_workers = 20
    process_infox_file(max_workers)
    max_threads = 100
    parse_all_files_and_save_to_excel(max_threads)
