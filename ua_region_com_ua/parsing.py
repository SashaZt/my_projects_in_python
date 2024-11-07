import json
import re
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from tqdm import tqdm

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
json_result = data_directory / "result.json"
edrpou_csv_file = data_directory / "edrpou.csv"
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
            # Находим метку (ключ) и данные (значение)
            label_element = item.find("span", class_="company-sidebar__label")
            data_element = item.find(
                "div", class_="company-sidebar__data") or item

            # Получаем текст метки
            label = label_element.get_text(
                strip=True) if label_element else None
            # Если data_element содержит ссылки, собираем текст всех ссылок
            if data_element.find("a"):
                data = ", ".join([a.get_text(strip=True)
                                  for a in data_element.find_all("a")])
            else:
                # Иначе просто берем текст из data_element
                data = data_element.get_text(strip=True).replace(
                    "\xa0", " ") if data_element else None

            # Сохраняем в словарь только если метка и данные найдены
            if label and data:
                company_data[label] = data

        return company_data

    # def extract_company_data(self, container):
    #     company_data = {}
    #     items = container.find_all("div", class_="company-sidebar__item")

    #     for item in items:
    #         label_element = item.find("span", class_="company-sidebar__label")
    #         data_element = item.find("div", class_="company-sidebar__data") or item

    #         # Извлекаем текст метки и данных, или устанавливаем None, если элемент не найден
    #         label = label_element.get_text(strip=True) if label_element else None
    #         data = (
    #             data_element.get_text(strip=True).replace("\xa0", " ")
    #             if data_element
    #             else None
    #         )

    #         # Добавляем данные в словарь, только если метка найдена
    #         if label:
    #             company_data[label] = data

    #     return company_data

    def parse_single_html(self, file_html):
        # logger.info(file_html)
        with open(file_html, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")
        company_data = {}

        # Извлечение заголовка и юридического адреса
        page_title_raw = soup.select_one("#main > div:nth-child(1) > div > h1")
        page_title = page_title_raw.get_text(
            strip=True) if page_title_raw else None
        containers = soup.select(
            ".px-md-4.pb-md-4.info_block.rounded.border.mt-3 > div.row > div.col-md-8 > div, "
            ".company-sidebar.p-3.p-md-4.mb-3.border"
        )

        for container in containers:
            company_data.update(self.extract_company_data(container))
        # Извлечение кодов КВЕД
        kved_elements = soup.select('a[href^="/kved/"]')
        kved_list = [element["href"].split(
            "/kved/")[1] for element in kved_elements]
        kved_string = ",".join(kved_list)

        # Добавляем в словарь полученные данные
        company_data["kved"] = kved_string
        company_data["page_title"] = page_title
        # company_data["legal_address"] = legal_address

        # Очистка текста
        cleaned_data = {key: self.clean_text(value)
                        for key, value in company_data.items()}
        return cleaned_data

    def parsing_html(self):
        all_files = self.list_html()
        # Инициализация прогресс-бараedrpou.csv
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
                    logger.error(f"Ошибка при обработке файла {
                                 file_html}: {e}")
                    # Добавление трассировки стека
                    logger.error(traceback.format_exc())
                finally:
                    # Обновляем прогресс-бар после завершения обработки каждого файла
                    progress_bar.update(1)

        # Закрываем прогресс-бар
        progress_bar.close()
        return all_results

    def load_processed_ids(self):
        # Загружаем идентификаторы из edrpou.csv, если файл существует
        if edrpou_csv_file.exists():
            # edrpou_df = pd.read_csv(edrpou_csv_file)
            edrpou_df = pd.read_csv(edrpou_csv_file, dtype={"edrpou": str})
            # Убираем только пробелы
            edrpou_df["edrpou"] = edrpou_df["edrpou"].str.strip()
            edrpou_set = set(edrpou_df["edrpou"])
            return edrpou_set
            # return set(
            #     edrpou_df["edrpou"].astype(str)
            # )  # Возвращаем множество идентификаторов
        else:
            logger.warning(
                f"Файл {edrpou_csv_file} не найден. Обрабатываем все файлы.")
            return None  # Возвращаем None, если файл отсутствует

    def list_html(self):
        # Получаем список идентификаторов, которые уже обработаны
        processed_ids = self.load_processed_ids()

        # Формируем список файлов
        if processed_ids is not None:
            # Если есть processed_ids, исключаем файлы с этими идентификаторами
            file_list = [
                file
                for file in html_files_directory.iterdir()
                if file.is_file() and file.stem not in processed_ids
            ]
        else:
            # Если processed_ids is None, берем все файлы
            file_list = [
                file for file in html_files_directory.iterdir() if file.is_file()
            ]

        logger.info(f"Всего файлов для обработки: {len(file_list)}")
        return file_list

    # def list_html(self):
    #     # Получаем список всех файлов в директории
    #     file_list = [file for file in html_files_directory.iterdir() if file.is_file()]
    #     logger.info(f"Всего компаний {len(file_list)}")
    #     return file_list

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

    def save_results_to_json(self, all_results):
        # Сохранить результаты в JSON файл
        try:
            with open(json_result, "w", encoding="utf-8") as json_file:
                json.dump(all_results, json_file, ensure_ascii=False, indent=4)
            logger.info(f"Данные успешно сохранены в файл {json_result}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных в файл {
                         json_result}: {e}")
            raise
