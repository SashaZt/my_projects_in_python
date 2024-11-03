from configuration.logger_setup import logger
from bs4 import BeautifulSoup
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import xml.etree.ElementTree as ET
import re

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


def parse_single_html():
    for html_file in html_files_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content: str = file.read()
        file_name = html_file.stem
        logger.info(file_name)
        soup = BeautifulSoup(content, "lxml")
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
        logger.info(cleaned_data)
    # return cleaned_data


def extract_company_data(container):
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


# def clean_text(text):
#     if text is None:
#         return None
#     return text.replace("\xa0", " ").strip()
def clean_text(text):
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


if __name__ == "__main__":
    parse_single_html()
