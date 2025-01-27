import json
import os
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup


def find_title(soup):
    selectors = [
        "#edrpou_main_conatiner > div.dr_main_content.dr_showokpo_c > div:nth-child(8) > div > div:nth-child(1) > div > div:nth-child(1) > div.dr_value_title",
        "#edrpou_main_conatiner > div.dr_main_content.dr_showokpo_c > div:nth-child(9) > div > div:nth-child(1) > div > div:nth-child(1) > div.dr_value_title",
    ]

    for selector in selectors:
        title_div = soup.select_one(selector)
        if title_div:
            return title_div.text.strip()

    return None
    # return title_div.text.strip() if title_div else None


def find_data_registr(soup):
    data_registr_div = soup.find(
        "div", class_="dr_value_subtitle", string="Дата реєстрації"
    )
    if data_registr_div:
        return data_registr_div.find_next("div", class_="dr_value").text.strip()
    return None


def find_record_number(soup):
    """"""
    record_number_div = soup.find(
        "div", class_="dr_value_subtitle", string="Номер запису"
    )
    if record_number_div:
        return record_number_div.find_next("div", class_="dr_value").text.strip()
    return None


def find_tax_debt(soup):
    debt_div = soup.find(
        "div",
        class_="dr_value_subtitle",
        string=lambda text: text and text.startswith("Податковий борг станом на"),
    )
    if debt_div:
        date = debt_div.text.split("на")[1].strip()
        dr_value_div = debt_div.find_next("div", class_="dr_value")
        if dr_value_div:
            # Проверяем, есть ли тег <t>, если нет - ищем текст напрямую
            t_element = dr_value_div.find("t")
            if t_element:
                status = t_element.text.strip()
            else:
                # Извлекаем текст, убирая возможные пробелы и переносы строк
                status = dr_value_div.get_text(strip=True, separator=" ")
                # Убираем все, что не цифры и не точка (для суммы)
                status = "".join(
                    [char for char in status if char.isdigit() or char == "."]
                )
                if (
                    status
                ):  # Если что-то нашли, используем это как статус, иначе "Відсутній"
                    status = status
                else:
                    status = "Відсутній"
            return date, status
    return None, None


def find_wage_arrears(soup):
    arrears_div = soup.find(
        "div",
        class_="dr_value_subtitle",
        string=lambda text: text
        and text.startswith("Заборгованість по заробітній платі станом на"),
    )
    if arrears_div:
        date = arrears_div.text.split("на")[1].strip()
        dr_value_div = arrears_div.find_next("div", class_="dr_value")
        if dr_value_div:
            t_element = dr_value_div.find("t")
            if t_element:
                status = t_element.text.strip()  # Случай с "Відсутня"
            else:
                # Извлекаем текст, убирая возможные пробелы и переносы строк
                status_text = dr_value_div.get_text(strip=True, separator=" ")
                # Ищем число, которое может быть суммой долга
                import re

                match = re.search(
                    r"\b(\d+(?:\.\d+)?)\s*(?:грн|грн\.|гривень)\b", status_text
                )
                if match:
                    status = match.group(1)  # Случай с суммой долга
                else:
                    status = "Відсутня"  # Если не нашли сумму, предполагаем нет долга
            return date, status
    return None, None


def find_registration(soup):
    # selectors = [
    #     "#edrpou_main_conatiner > div.dr_main_content.dr_showokpo_c > div:nth-child(8) > div > div:nth-child(1) > div > div:nth-child(2) > div.dr_value_state.dr_green",
    #     "#edrpou_main_conatiner > div.dr_main_content.dr_showokpo_c > div:nth-child(9) > div > div:nth-child(1) > div > div:nth-child(2) > div.dr_value_state.dr_green",
    #     "#edrpou_main_conatiner > div.dr_main_content.dr_showokpo_c > div:nth-child(8) > div > div:nth-child(1) > div > div:nth-child(2) > div.dr_value_state.dr_orange"
    #     "#edrpou_main_conatiner > div.dr_main_content.dr_showokpo_c > div:nth-child(9) > div > div:nth-child(1) > div > div:nth-child(2) > div.dr_value_state.dr_orange"
    # ]
    # for selector in selectors:
    #     title_div = soup.select_one(selector)
    #     if title_div:
    #         return title_div.text.strip()
    selectors = [
        "#edrpou_main_conatiner .dr_value_state.dr_green",
        "#edrpou_main_conatiner .dr_value_state.dr_orange"
    ]
    
    for selector in selectors:
        title_divs = soup.select(selector)
        if title_divs:
            text = title_divs[0].text.strip()
            print(text)
            return text
    
    return None
    # if registration_tag is None:
    #     return None  # Возвращаем None, если элемент не найден
    # registration = registration_tag.get_text(strip=True)
    # return registration


def process_html_file(file_path, combined_data):

    with open(file_path, "r", encoding="utf-8") as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, "html.parser")
    main_code, additional_codes = extract_kved_codes(soup)
    # Получаем имя файла без расширения
    filename = get_filename_without_extension(file_path)

    # Ищем соответствие в combined_data
    edrpo, address = find_edrpo_and_address(combined_data, filename)
    tax_debt_date, tax_debt_status = find_tax_debt(soup)
    arrears_date, arrears_status = find_wage_arrears(soup)
    title = find_title(soup)
    registration = find_registration(soup)
    if title is None:
        return None
    return {
        "title": title,
        "registration": registration,
        "data_registr": find_data_registr(soup),
        "record_number": find_record_number(soup),
        "tax_debt_date": tax_debt_date,
        "tax_debt_status": tax_debt_status,
        "arrears_date": arrears_date,
        "arrears_status": arrears_status,
        "main_code": main_code,
        "additional_codes": additional_codes,
        "edrpo": edrpo,
        "address": address,
    }


def extract_kved_codes(soup):
    kved_block = soup.find(
        "div", string=lambda text: text and "Види діяльності" in text
    )
    if not kved_block:
        return None, None

    # Находим общий блок с КВЕДами
    parent_div = kved_block.find_parent("div", class_="dr_column")

    # Поиск основного КВЕДа в следующем блоке
    next_dr_column = parent_div.find_next("div", class_="dr_column")
    if next_dr_column:
        main_kved_div = next_dr_column.find(
            "div", string=lambda text: text and "Код КВЕД" in text
        )
        if main_kved_div:
            main_code = main_kved_div.text.split("Код КВЕД")[1].strip().split()[0]
        else:
            main_code = None
    else:
        main_code = None

    # Поиск всех дополнительных КВЕДов, включая те, что в collapse блоке
    additional_codes = []
    for div in next_dr_column.find_all(
        "div",
        class_="dr_value dr_margin_value",
        string=lambda text: text and text[0].isdigit(),
    ):
        code = div.text.split()[0]  # Предполагаем, что код идет первым в строке
        if (
            code != main_code
        ):  # Чтобы не дублировать основной код, если он совпадает с дополнительным
            additional_codes.append(code)

    return main_code, ",".join(additional_codes) if additional_codes else None


def load_combined_data(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_filename_without_extension(file_path):
    return Path(file_path).stem


def find_edrpo_and_address(combined_data, tax_number):
    for entry in combined_data:
        if entry.get("taxNumber") == tax_number:
            return entry.get("edrpo"), entry.get("address")
    return None, None


def save_to_excel(results):
    # Преобразуем список словарей в DataFrame
    df = pd.DataFrame(results)

    # Указываем путь и имя файла для сохранения
    excel_file = Path.cwd() / "output.xlsx"

    # Сохраняем DataFrame в Excel файл
    df.to_excel(excel_file, index=False)


def main():
    current_directory = Path.cwd()
    html_directory = current_directory / "html"
    combined_data_file = current_directory / "combined_data.json"

    # Загрузка combined_data.json
    combined_data = load_combined_data(combined_data_file)

    results = []

    # for html_file in list(html_directory.glob("*.html"))[:20]:
    for html_file in html_directory.glob("*.html"):
        # print(html_file)
        data = process_html_file(html_file, combined_data)
        if data:  # Проверяем, что данные не пустые
            results.append(data)

    # Здесь вы можете добавить логику для записи или дальнейшей обработки результатов
    save_to_excel(results)


if __name__ == "__main__":
    main()
