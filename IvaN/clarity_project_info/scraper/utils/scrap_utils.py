from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import pandas as pd
from bs4 import BeautifulSoup
from config.logger import logger
from tqdm import tqdm

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
data_directory = current_directory / "data"

html_files_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)


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
    codes = [
        "2355",
        "2465",
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
