import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from logger import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)


def get_html():
    cookies = {
        "JSESSIONID": "fDYLuKWRAnxVCFPeXgbiZRnCGR5IhDDCNJ_IRPw_.msc01-popp01:main-popp",
    }

    headers = {
        "Accept": "application/xml, text/xml, */*; q=0.01",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Faces-Request": "partial/ajax",
        "Origin": "http://zakupki.gov.kg",
        "Referer": "http://zakupki.gov.kg/popp/view/order/winners.xhtml",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    params = {
        "cid": "2",
    }
    for i in range(0, 5000):
        table_first = str(i * 10)
        output_html_file = html_directory / f"data_{table_first}.html"

        data = {
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": "table",
            "javax.faces.partial.execute": "table",
            "javax.faces.partial.render": "table",
            "table": "table",
            "table_pagination": "true",
            "table_first": table_first,
            "table_rows": "10",
            "table_skipChildren": "true",
            "table_encodeFeature": "true",
            "form": "form",
            "javax.faces.ViewState": "-8024986581166610087:8952900499363807765",
        }
        if output_html_file.exists():
            logger.info(f"File {output_html_file} already exists. Skipping download.")
            continue
        response = requests.post(
            "http://zakupki.gov.kg/popp/view/order/winners.xhtml",
            params=params,
            cookies=cookies,
            headers=headers,
            data=data,
            verify=False,
            timeout=30,
        )

        # Проверка кода ответа
        if response.status_code == 200:

            # Сохранение HTML-страницы целиком
            with open(output_html_file, "w", encoding="utf-8") as file:
                file.write(response.text)
            logger.info(f"Successfully saved {output_html_file}")
        else:
            logger.error(f"Failed to get HTML. Status code: {response.status_code}")


def parse_file(file_path):
    """Парсит один XML файл и извлекает данные из таблицы"""

    print(f"Обрабатываем файл: {file_path}")

    # Открываем и читаем файл
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Создаем объект BeautifulSoup с XML-парсером
    soup = BeautifulSoup(content, "xml")

    # Находим CDATA в update с id="table"
    update_element = soup.find("update", id="table")
    if not update_element:
        print(f"Не найден элемент 'update' с id='table' в файле {file_path}")
        return []

    # Извлекаем данные из CDATA
    cdata = update_element.string
    if not cdata:
        print(f"Нет данных CDATA в элементе update в файле {file_path}")
        return []

    # Парсим HTML из CDATA
    html_soup = BeautifulSoup(cdata, "html.parser")

    # Находим все строки таблицы
    all_ad = html_soup.find_all(
        "tr", class_=re.compile(r"ui-widget-content ui-datatable-(even|odd)")
    )

    print(f"Найдено строк в таблице: {len(all_ad)}")

    all_data = []
    for ad in all_ad:
        # Находим все ячейки в строке
        td_elements = ad.find_all("td")

        if len(td_elements) >= 10:  # Проверяем, что достаточно элементов
            # Извлекаем данные
            serial_number = td_elements[0].get_text(strip=True).replace("№", "").strip()

            # Используем регулярное выражение, чтобы избавиться от "Номер объявления" и любых пробелов
            ad_number_text = td_elements[1].get_text(strip=True)
            ad_number = re.sub(r"Номер объявления\s*", "", ad_number_text).strip()

            name_of_purchase_text = td_elements[2].get_text(strip=True)
            name_of_purchase = re.sub(
                r"Наименование закупки\s*", "", name_of_purchase_text
            ).strip()

            winners_names_text = td_elements[3].get_text(strip=True)
            winners_names = re.sub(
                r"Наименования победителя\s*", "", winners_names_text
            ).strip()

            lot_number_text = td_elements[4].get_text(strip=True)
            lot_number = re.sub(r"Номер лота\s*", "", lot_number_text).strip()

            planned_sum_text = td_elements[5].get_text(strip=True)
            planned_sum_clean = re.sub(
                r"Планируемая сумма лота\s*", "", planned_sum_text
            ).strip()
            # Ищем числа с пробелами (например, "80 000", "121 180")
            planned_sum_values = re.findall(r"\d+\s\d+", planned_sum_clean)
            planned_sum = ", ".join(planned_sum_values)

            # Обработка "Цена предложенная участником"
            offered_price_text = td_elements[6].get_text(strip=True)
            offered_price_clean = re.sub(
                r"Цена предложенная участником\s*", "", offered_price_text
            ).strip()
            offered_price_values = re.findall(r"\d+\s\d+", offered_price_clean)
            offered_price = ", ".join(offered_price_values)

            # Обработка "Цена контракта"
            contract_price_text = td_elements[7].get_text(strip=True)
            contract_price_clean = re.sub(
                r"Цена контракта\s*", "", contract_price_text
            ).strip()
            contract_price_values = re.findall(r"\d+\s\d+", contract_price_clean)
            contract_price = ", ".join(contract_price_values)
            contract_number_text = td_elements[8].get_text(strip=True)
            contract_number = re.sub(
                r"Номер контракта\s*", "", contract_number_text
            ).strip()

            contract_signing_date_text = td_elements[9].get_text(strip=True)
            contract_signing_date = re.sub(
                r"Дата подписания контракта\s*", "", contract_signing_date_text
            ).strip()

            # Создаем словарь с данными
            data = {
                "№": serial_number,
                "Номер объявления": ad_number,
                "Наименование закупки": name_of_purchase,
                "Наименования победителя": winners_names,
                "Номер лота": lot_number,
                "Планируемая сумма лота": planned_sum,
                "Цена предложенная участником": offered_price,
                "Цена контракта": contract_price,
                "Номер контракта": contract_number,
                "Дата подписания контракта": contract_signing_date,
            }
            all_data.append(data)
        else:
            print(f"Недостаточно элементов td в строке: {len(td_elements)}")

    return all_data


def parsing_files():
    # Путь к директории с файлами
    input_directory = "."  # Текущая директория, измените на вашу директорию с файлами

    all_data = []
    file_count = 0

    # Шаблоны файлов, которые нужно обработать
    patterns = ["*.html", "*.txt"]  # Добавьте нужные расширения

    for pattern in patterns:
        for file_path in Path(html_directory).glob(pattern):
            try:
                file_data = parse_file(file_path)
                all_data.extend(file_data)
                file_count += 1
                print(
                    f"Успешно обработан файл {file_path}, добавлено {len(file_data)} записей"
                )
            except Exception as e:
                print(f"Ошибка при обработке файла {file_path}: {str(e)}")

    if all_data:
        # Создаем DataFrame и сохраняем в Excel
        df = pd.DataFrame(all_data)
        df.to_excel("output.xlsx", index=False)
        print(
            f"Данные успешно сохранены в output.xlsx. Всего записей: {len(all_data)} из {file_count} файлов"
        )
    else:
        print("Не удалось извлечь данные из файлов.")


if __name__ == "__main__":
    get_html()
    parsing_files()
