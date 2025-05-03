import re
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
# html_files_directory = current_directory / "html_files_edrpo"
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
        # Для каждой обработки выбираем свою функцию парсинга
        # result = parse_html_file(file)
        result = parse_html_file_edrpo(file)

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


def parse_html_file_edrpo(file_path):
    with open(file_path, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")
    data = {}

    # Список полей для извлечения
    fields = [
        "ЄДРПОУ",
        "Назва",
        "Організаційна форма",
        "Адреса",
        "Стан",
        "Дата реєстрації",
        "Уповноважені особи",
        "Види діяльності",
        "Контакти",
    ]

    # Проходим по строкам таблицы
    table = soup.find("table")
    if not table:
        return data  # Возвращаем пустой словарь, если таблица не найдена

    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) == 2:
            label = cells[0].text.strip().replace(":", "").strip()
            if label in fields:
                if label == "Види діяльності":
                    # Проверяем наличие элемента
                    activity_div = cells[1].find("div", class_="company-activity-list")
                    if activity_div:
                        activity_item = activity_div.find("div", class_="activity-item")
                        if activity_item:
                            activity = activity_item.text.strip()
                            # Убираем лишние пробелы и добавляем пробел после кода
                            activity = re.sub(r"\s+", " ", activity).strip()
                            code = activity[:5]  # Код (например, 69.10)
                            description = activity[5:]  # Описание
                            data[label] = f"{code} {description}"
                        else:
                            data[label] = None
                    else:
                        data[label] = None
                elif label == "Назва":
                    # Извлекаем основной текст, если он есть
                    main_name = (
                        cells[1].contents[0].strip() if cells[1].contents else None
                    )
                    data[label] = main_name
                    # Проверяем наличие сокращенной названия в <div class="small">
                    small_title_tag = cells[1].find("div", class_="small")
                    if small_title_tag:
                        small_title = small_title_tag.text.strip()
                        data["Коротка назва"] = small_title.replace("(", "").replace(
                            ")", ""
                        )
                    else:
                        data["Коротка назва"] = None
                elif label == "Адреса":
                    # Извлекаем основной адрес, если он есть
                    main_address = (
                        cells[1].contents[0].strip() if cells[1].contents else None
                    )
                    data[label] = main_address
                elif label == "Уповноважені особи":
                    # Проверяем наличие имени и должности
                    person_link = cells[1].find("a")
                    person_role = cells[1].find("span", class_="text-secondary")
                    if person_link and person_role:
                        person = (
                            f"{person_link.text.strip()} - {person_role.text.strip()}"
                        )
                        data[label] = person
                    else:
                        data[label] = None
                elif label == "Контакти":
                    # Инициализируем списки для телефонов и email
                    data["Телефони"] = []
                    data["Email"] = []
                    # Находим все div с классом mb-5
                    contact_divs = cells[1].find_all("div", class_="mb-5")
                    for div in contact_divs:
                        # Проверяем наличие телефона
                        phone_link = div.find("a", href=re.compile(r"^tel:"))
                        if phone_link:
                            phone = phone_link.text.strip()
                            data["Телефони"].append(phone)
                        # Проверяем наличие email
                        email_link = div.find("a", href=re.compile(r"^mailto:"))
                        if email_link:
                            email = email_link.text.strip()
                            data["Email"].append(email)
                    # Если списки пустые, присваиваем None; если не пустые, преобразуем в строку
                    data["Телефони"] = (
                        ", ".join(data["Телефони"]) if data["Телефони"] else None
                    )
                    data["Email"] = ", ".join(data["Email"]) if data["Email"] else None

                elif label == "Стан":
                    # Проверяем наличие статуса
                    status_div = cells[1].find(
                        "div", class_=["text-primary", "text-danger"]
                    )
                    if status_div:
                        # Извлекаем текст состояния, убирая иконки и лишние пробелы
                        status_text = status_div.text.strip()
                        # Удаляем возможные иконки или другие символы
                        status_text = re.sub(r"[\n\t]+", " ", status_text).strip()
                        data[label] = status_text
                    else:
                        data[label] = None
                    # Проверяем наличие даты
                    date_text = cells[1].text.strip()
                    date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", date_text)
                    data["Дата стану"] = date_match.group(0) if date_match else None
                else:
                    # Для остальных полей извлекаем текст, если он есть
                    text = cells[1].text.strip()
                    data[label] = text.split("\n")[0].strip() if text else None

    return data
