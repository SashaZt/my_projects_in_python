from configuration.logger_setup import logger
from bs4 import BeautifulSoup
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd
import xml.etree.ElementTree as ET
import re
import traceback

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"

html_files_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

output_csv_file = data_directory / "output.csv"
csv_file_successful = data_directory / "identifier_successful.csv"
xlsx_result = data_directory / "result.xlsx"
# file_proxy = configuration_directory / "roman.txt"


class Parsing:

    def __init__(self, html_files_directory, xlsx_result, max_workers) -> None:
        self.html_files_directory = html_files_directory
        self.xlsx_result = xlsx_result
        self.max_workers = max_workers

    # Функция для извлечения данных из контейнера

    def extract_company_data(self, container):
        company_data = {}
        items = container.find_all("div", class_="company-sidebar__item")

        for item in items:
            label_element = item.find("span", class_="company-sidebar__label")
            data_element = item.find("div", class_="company-sidebar__data") or item

            # Извлекаем текст метки и данных, или устанавливаем None, если элемент не найден
            label = label_element.get_text(strip=True) if label_element else None
            data = (
                data_element.get_text(strip=True).replace("\xa0", " ")
                if data_element
                else None
            )

            # Добавляем данные в словарь, только если метка найдена
            if label:
                company_data[label] = data

        return company_data

    def parse_single_html(self, file_html):
        # logger.info(file_html)
        with open(file_html, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")
        company_data = {}

        # Безопасное извлечение заголовка страницы
        page_title_raw = soup.select_one("#main > div:nth-child(1) > div > h1")
        page_title = page_title_raw.get_text(strip=True) if page_title_raw else None

        # Безопасное извлечение юридического адреса
        legal_address_raw = soup.select_one(
            "#main > div.cart-company-full.container.pb-5 > div.row.flex-row-reverse > div.col-xl-9 > div.px-3.pb-3.px-md-4.pb-md-4.info_block.rounded.border.mt-3 > div.row > div.col-md-8 > div > div:nth-child(2) > div"
        )
        legal_address = (
            legal_address_raw.get_text(strip=True) if legal_address_raw else None
        )
        # Список возможных селекторов для контейнеров
        selectors = [
            "#main > div.cart-company-full.container.pb-5 > div.row.flex-row-reverse > div.col-xl-9 > div.px-3.pb-3.px-md-4.pb-md-4.info_block.rounded.border.mt-3 > div > div.col-md-4.mt-4.company-sidebar-info > div.company-sidebar.border.rounded.p-3.p-md-4.mb-3",
            "#main > div.cart-company-full.container.pb-5 > div.row.flex-row-reverse > div.col-xl-9 > div.px-3.pb-3.px-md-4.pb-md-4.info_block.rounded.border.mt-3 > div.row > div.col-md-8 > div",
            "#main > div.cart-company-full.container.pb-5 > div.row.flex-row-reverse > div.d-none.d-xl-block.col-xl-3.company-item-sidebar > div.d-none.d-lg-block.company-sidebar.p-3.p-md-4.mb-3.border",
            "#main > div.cart-company-full.container.pb-5 > div.row.flex-row-reverse > div.d-none.d-xl-block.col-xl-3.company-item-sidebar > div.d-none.d-lg-block.company-sidebar.p-3.p-md-4.mb-3.border",
            "#main > div.cart-company-full.container.pb-5 > div > div.col-xl-9 > div.col-md-4.mt-4.company-sidebar-info > div.company-sidebar.border.rounded.p-3.p-md-4.mb-3",  # Добавил
            "#main > div.cart-company-full.container.pb-5 > div > div.col-xl-9 > div.px-3.pb-3.px-md-4.pb-md-4.info_block.rounded.border.mt-3",  # Добавил
        ]
        # Ищем контейнеры по каждому селектору
        for selector in selectors:
            container = soup.select_one(selector)
            if container:
                # Обновляем company_data, добавляя данные из найденного контейнера
                company_data.update(self.extract_company_data(container))

        # Словарь для текущей единицы данных
        # Извлекаем коды КВЕД
        kved_elements = soup.select('a[href^="/kved/"]')
        kved_list = [element["href"].split("/kved/")[1] for element in kved_elements]
        kved_string = ",".join(kved_list)

        # Добавляем коды КВЕД в словарь
        company_data["kved"] = kved_string
        company_data["page_title"] = page_title
        company_data["legal_address"] = legal_address

        # logger.info(company_data)
        cleaned_data = {
            key: self.clean_text(value) for key, value in company_data.items()
        }
        return cleaned_data

    def parsing_html(self):
        all_files = self.list_html()
        # Инициализация прогресс-бара
        total_urls = len(all_files)
        progress_bar = tqdm(
            total=total_urls,
            desc="Обработка файлов",
            bar_format="{l_bar}{bar} | Время: {elapsed} | Осталось: {remaining} | Скорость: {rate_fmt}",
        )

        # Многопоточная обработка файлов
        all_results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.parse_single_html, file_html): file_html
                for file_html in all_files
            }

            # Сбор результатов по мере завершения каждого потока
            for future in as_completed(futures):
                file_html = futures[future]
                try:
                    result = future.result()
                    all_results.append(result)
                except Exception as e:
                    logger.error(f"Ошибка при обработке файла {file_html}: {e}")
                    logger.error(traceback.format_exc())  # Добавление трассировки стека
                finally:
                    # Обновляем прогресс-бар после завершения обработки каждого файла
                    progress_bar.update(1)

        # Закрываем прогресс-бар
        progress_bar.close()
        return all_results

    def list_html(self):
        # Получаем список всех файлов в директории
        file_list = [file for file in html_files_directory.iterdir() if file.is_file()]
        logger.info(f"Всего компаний {len(file_list)}")
        return file_list

    # Функция для очистки данных

    def clean_text(self, text):
        # Проверяем, что text не равен None
        if text is None:
            return None

        # Убираем лишние пробелы и символы \xa0
        cleaned_text = text.replace("\xa0", " ").strip()

        # Если текст не содержит ключевые слова, возвращаем его без изменений
        if not any(
            keyword in cleaned_text
            for keyword in [
                "Код ЄДРПОУ",
                "Дата реєстрації",
                "Дата оновлення",
                "Кількість працівників",
                "Дата реєстрації",
            ]
        ):
            return cleaned_text

        # Убираем заголовки, если они присутствуют
        cleaned_text = re.sub(
            r"^(Код ЄДРПОУ|Дата реєстрації|Дата оновлення|Кількість працівників)",
            "",
            cleaned_text,
        )

        return cleaned_text.strip()

    def write_to_excel(self, all_results):
        if not all_results:
            print("Нет данных для записи.")
            return

        df = pd.DataFrame(all_results)
        df.to_excel("output.xlsx", index=False, sheet_name="Data")
