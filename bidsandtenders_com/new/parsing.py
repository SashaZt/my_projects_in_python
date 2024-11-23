import json
import re
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import phonenumbers
import usaddress
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from tqdm import tqdm

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
data_directory = current_directory / "data"
json_directory = current_directory / "json"
configuration_directory = current_directory / "configuration"

json_directory.mkdir(parents=True, exist_ok=True)
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

    def extract_phone_company(self, soup):
        phone_tags = soup.select(
            "#__next > div > section > section > div > div > div > div > div > div > div > div:nth-child(2) > div > p"
        )
        for tag in phone_tags:
            phone_text = tag.get_text(strip=True)
            if re.search(r"^[+\d\s-]+$", phone_text):
                phone = self.normalize_phone_number(phone_text)
                return phone
        return None

    def extract_name_company(self, soup):
        name_tag = soup.select_one(
            "#__next > div > section > section > div > div > div > div > div > div > div > div:nth-child(1) > h1 > span"
        )
        return name_tag.get_text(strip=True) if name_tag else None

    def extract_address_company(self, soup):
        address_tag = soup.select_one(
            "#__next > div > section > section > div > div > div > div > div > div > div > div:nth-child(1) > div > a > p > span"
        )
        return address_tag.get_text(strip=True) if address_tag else None

    def extract_company_size(self, soup):
        company_size_tag = soup.find(
            "p", {"data-test-id": "business-profile-nav-about-company-size"}
        )
        return (
            company_size_tag.get_text(strip=True).replace("Company Size: ", "")
            if company_size_tag
            else None
        )

    def extract_average_contract_size(self, soup):
        average_contract_size_tag = soup.find(
            "p", {"data-test-id": "business-profile-nav-about-avg-contract-size"}
        )
        return (
            average_contract_size_tag.get_text(strip=True).replace(
                "Average Contract Size: ", ""
            )
            if average_contract_size_tag
            else None
        )

    def extract_company_types(self, soup):
        company_types_tag = soup.find(
            "p", {"data-test-id": "business-profile-nav-about-business-types"}
        )
        return company_types_tag.get_text(strip=True) if company_types_tag else None

    def extract_trades_and_services(self, soup):
        # Поиск по заголовку "Trades and Services", чтобы получить следующий элемент с информацией
        trades_and_services_header = soup.find("h2", string="Trades and Services")
        if trades_and_services_header:
            trades_and_services_tag = trades_and_services_header.find_next(
                "span", {"data-test-id": "expandable-text"}
            )
            if trades_and_services_tag:
                nested_span = trades_and_services_tag.find("span")
                return nested_span.get_text(strip=True) if nested_span else None
        return None

    def extract_web_site_company(self, soup):
        website_tag = soup.find("a", {"data-test-id": "website-link"})
        return website_tag["href"] if website_tag else None

    def extract_service_areas(self, soup):
        service_areas_tag = soup.select_one(
            "#service-areas > map > div > div > div > p"
        )
        return service_areas_tag.get_text(strip=True) if service_areas_tag else None

    def get_file_name(self, file_path):
        return Path(file_path).stem

    def normalize_phone_number(self, phone_number):
        try:
            # Парсим номер телефона
            parsed_number = phonenumbers.parse(phone_number, "US")

            # Приводим номер к международному формату (E.164)
            formatted_number = phonenumbers.format_number(
                parsed_number, phonenumbers.PhoneNumberFormat.E164
            )

            return formatted_number
        except phonenumbers.NumberParseException:
            # Обработка ошибок, если номер не удается распарсить
            return None

    def clean_address(self, address):
        # Убираем лишние слова, которые могут вызывать ошибку
        parts = address.split(",")
        unique_parts = []
        seen = set()

        for part in parts:
            cleaned_part = part.strip().lower()
            if cleaned_part not in seen and not re.search(
                r"\d{5}(?:-\d{4})?$", cleaned_part
            ):
                seen.add(cleaned_part)
                unique_parts.append(part.strip())

        return ", ".join(unique_parts)

    def split_address_usaddress(self, address):
        try:
            # Очищаем адрес перед разбором
            cleaned_address = self.clean_address(address)

            # Разбираем адрес с помощью usaddress
            parsed_address, address_type = usaddress.tag(cleaned_address)

            # Определяем компоненты адреса
            number = parsed_address.get("AddressNumber", "")
            street = " ".join(
                [
                    parsed_address.get("StreetNamePreDirectional", ""),
                    parsed_address.get("StreetName", ""),
                    parsed_address.get("StreetNamePostType", ""),
                    parsed_address.get("OccupancyType", ""),
                    parsed_address.get("OccupancyIdentifier", ""),
                ]
            ).strip()
            city = parsed_address.get("PlaceName", "")
            state = parsed_address.get("StateName", "")

            # Возвращаем разделенный адрес как словарь
            return {"number": number, "street": street, "city": city, "state": state}
        except usaddress.RepeatedLabelError as e:
            logger.error(f"Ошибка разбора адреса: {address}")
            return None

    def parse_single_html(self, file_html):
        file_name_json = self.get_file_name(file_html)
        # Открытие и чтение HTML-файла
        with open(file_html, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")

        script_tags = soup.find("script", type="application/json")
        # Извлекаем содержимое и парсим его как JSON
        if script_tags:
            json_content = json.loads(script_tags.string)
            json_file = json_directory / f"{file_name_json}.json"
            # Сохраняем данные в JSON файл
            with open(json_file, "w", encoding="utf-8") as json_file:
                json.dump(json_content, json_file, indent=4, ensure_ascii=False)

        # Извлекаем данные с помощью функций
        phone_company = self.extract_phone_company(soup)
        name_company = self.extract_name_company(soup)
        adress_company = self.extract_address_company(soup)
        company_size = self.extract_company_size(soup)
        average_contract_size = self.extract_average_contract_size(soup)
        company_types = self.extract_company_types(soup)
        trades_and_services = self.extract_trades_and_services(soup)
        web_site_company = self.extract_web_site_company(soup)
        service_areas = self.extract_service_areas(soup)
        split_address = (
            self.split_address_usaddress(adress_company) if adress_company else None
        )
        number = split_address["number"] if split_address else None
        street = split_address["street"] if split_address else None
        city = split_address["city"] if split_address else None
        state = split_address["state"] if split_address else None
        # Собираем все данные в словарь
        company_data = {
            "phone_company": phone_company,
            "name_company": name_company,
            "address_number": number,
            "address_street": street,
            "address_city": city,
            "address_state": state,
            "company_size": company_size,
            "average_contract_size": average_contract_size,
            "company_types": company_types,
            "trades_and_services": trades_and_services,
            "web_site_company": web_site_company,
            "service_areas": service_areas,
        }
        return company_data
        # Сохраняем данные в JSON файл
        with open("company_data.json", "w", encoding="utf-8") as json_file:
            json.dump(company_data, json_file, indent=4, ensure_ascii=False)

        print("Данные успешно сохранены в файл company_data.json")

        # script_tags = soup.find("script", type="application/json")
        # # Извлекаем содержимое и парсим его как JSON
        # if script_tags:
        #     json_content = json.loads(script_tags.string)

        #     # name_company = json_content["props"][""]
        #     # Записываем json_content в файл
        #     with open("data.json", "w", encoding="utf-8") as json_file:
        #         json.dump(json_content, json_file, indent=4, ensure_ascii=False)
        # else:
        #     print("Тег <script> с type='application/json' не найден")

        # for script_tag in script_tags:
        #     try:
        #         data = json.loads(script_tag.string)
        #         if isinstance(data, dict):
        #             if (
        #                 "productPopularityLabel" in data
        #                 and "label" in data["productPopularityLabel"]
        #             ):
        #                 label_text = data["productPopularityLabel"]["label"]
        #                 match = re.search(r"(\d+)", label_text)
        #                 if match:
        #                     sales_product = int(match.group(1))
        #                     break
        # # Инициализация словаря для данных
        # data = {}

        # # Извлечение данных из "Таблица 1"
        # table_01 = soup.find("div", {"id": "profile-overview"})
        # if table_01:
        #     data["Название"] = table_01.find("h2").text.strip()

        #     # Извлечение списка данных
        #     items = table_01.find_all("li")
        #     additional_info_counter = 1
        #     for item in items:
        #         text = item.text.strip()
        #         if text.startswith("Статус:"):
        #             data["Статус"] = text.replace("Статус:", "").strip()
        #         elif text.startswith("ИНН:"):
        #             data["ИНН"] = text.replace("ИНН:", "").strip()
        #         elif text.startswith("Директор:"):
        #             data["Директор"] = text.replace("Директор:", "").strip()
        #         elif "Последнее обновление на сайте:" in text:
        #             data["Последнее обновление"] = text.replace(
        #                 "Последнее обновление на сайте:", ""
        #             ).strip()
        #         else:
        #             # Каждую строку "Дополнительной информации" добавляем в словарь с уникальным ключом
        #             key = f"Дополнительная информация {additional_info_counter}"
        #             data[key] = text
        #             additional_info_counter += 1

        # # Извлечение данных из "Таблица 2"
        # table_02 = soup.find("table", {"class": "table table-striped"})
        # if table_02:
        #     table_rows = table_02.find_all("tr")
        #     for row in table_rows:
        #         cells = row.find_all("td")
        #         if len(cells) == 2:
        #             key = cells[0].text.strip()
        #             value = cells[1].text.strip()
        #             # Удаление ненужных ссылок из таблицы (например, "Авторизуйтесь для просмотра")
        #             if "<a" in value:
        #                 value = BeautifulSoup(value, "lxml").text.strip()
        #             # Убираем лишние пробелы и переносы строк
        #             value = " ".join(value.split())
        #             data[key] = value if value else "-"
        # return data

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
            logger.error(f"Ошибка при сохранении данных в файл {json_result}: {e}")
            raise
