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
            data_element = item.find("div", class_="company-sidebar__data") or item

            # Получаем текст метки
            label = label_element.get_text(strip=True) if label_element else None
            # Если data_element содержит ссылки, собираем текст всех ссылок
            if data_element.find("a"):
                data = ", ".join(
                    [a.get_text(strip=True) for a in data_element.find_all("a")]
                )
            else:
                # Иначе просто берем текст из data_element
                data = (
                    data_element.get_text(strip=True).replace("\xa0", " ")
                    if data_element
                    else None
                )

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
        # Открытие и чтение HTML-файла
        with open(file_html, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")

        # Инициализация словаря для данных
        data = {}

        # Извлечение данных из "Таблица 1"
        table_01 = soup.find("div", {"id": "profile-overview"})
        if table_01:
            data["Название"] = table_01.find("h2").text.strip()

            # Извлечение списка данных
            items = table_01.find_all("li")
            additional_info_counter = 1
            for item in items:
                text = item.text.strip()
                if text.startswith("Статус:"):
                    data["Статус"] = text.replace("Статус:", "").strip()
                elif text.startswith("ИНН:"):
                    data["ИНН"] = text.replace("ИНН:", "").strip()
                elif text.startswith("Директор:"):
                    data["Директор"] = text.replace("Директор:", "").strip()
                elif "Последнее обновление на сайте:" in text:
                    data["Последнее обновление"] = text.replace(
                        "Последнее обновление на сайте:", ""
                    ).strip()
                else:
                    # Каждую строку "Дополнительной информации" добавляем в словарь с уникальным ключом
                    key = f"Дополнительная информация {additional_info_counter}"
                    data[key] = text
                    additional_info_counter += 1

        # Извлечение данных из "Таблица 2"
        table_02 = soup.find("table", {"class": "table table-striped"})
        if table_02:
            table_rows = table_02.find_all("tr")
            for row in table_rows:
                cells = row.find_all("td")
                if len(cells) == 2:
                    key = cells[0].text.strip()
                    value = cells[1].text.strip()
                    # Удаление ненужных ссылок из таблицы (например, "Авторизуйтесь для просмотра")
                    if "<a" in value:
                        value = BeautifulSoup(value, "lxml").text.strip()
                    # Убираем лишние пробелы и переносы строк
                    value = " ".join(value.split())
                    data[key] = value if value else "-"
        return data

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
                    logger.error(f"Ошибка при обработке файла {file_html}: {e}")
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
            logger.warning(f"Файл {edrpou_csv_file} не найден. Обрабатываем все файлы.")
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

    def write_to_excel(self):
        with json_result.open(encoding="utf-8") as file:
            # Прочитать содержимое JSON файла
            data = json.load(file)
        if not data:
            print("Нет данных для записи.")
            return

        df = pd.DataFrame(data)
        df.to_excel("output.xlsx", index=False, sheet_name="Data")

    def save_results_to_json(self, all_results):
        # Сохранить результаты в JSON файл
        try:
            with open(json_result, "w", encoding="utf-8") as json_file:
                json.dump(all_results, json_file, ensure_ascii=False, indent=4)
            logger.info(f"Данные успешно сохранены в файл {json_result}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных в файл {json_result}: {e}")
            raise
