import concurrent.futures
import json
import os
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)


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
    selectors = [
        "#edrpou_main_conatiner .dr_value_state.dr_green",
        "#edrpou_main_conatiner .dr_value_state.dr_orange",
    ]

    for selector in selectors:
        title_divs = soup.select(selector)
        if title_divs:
            text = title_divs[0].text.strip()
            # print(text)
            return text

    return None


def get_registration_date(soup):
    date_element = soup.find("div", string="Дата реєстрації")
    if date_element:
        date_value = date_element.find_next("div", class_="dr_value")
        return date_value.text.strip() if date_value else None
    return None


def get_authorized_person(soup):
    person_element = soup.find("div", string="Уповноважені особи")
    if person_element:
        name_span = person_element.find_next("span")
        return name_span.text.strip() if name_span else None
    return None


def get_inn(soup):
    person_element = soup.find("div", string="Індивідуальний податковий номер")
    if person_element:
        name_span = person_element.find_next("div")
        return name_span.text.strip() if name_span else None
    return None


def get_founder(soup):
    founder_element = soup.find(
        "div", class_="dr_value_subtitle", id="anchor_zasovniki"
    )
    if founder_element:
        founder_value = founder_element.find_next("div", class_="dr_value")
        return founder_value.text.strip() if founder_value else None
    return None


def get_statutory_fund(soup):
    # Ищем сначала div с классом dr_value_small
    fund_elements = soup.find_all("div", class_="dr_value_small")

    for element in fund_elements:
        # Проверяем, есть ли нужный текст в элементе
        if "Розмір внеску до статутного фонду:" in element.text:
            # Находим тег b внутри этого элемента
            b_tag = element.find("b")
            if b_tag:
                # Извлекаем текст до (100%)
                amount = b_tag.text.split("(")[0].strip()
                # Убираем лишние пробелы
                return " ".join(amount.split())
    return None


def get_mini_title(soup):
    title = soup.find("h1", class_="dr_title_3")
    if title:
        # Получаем весь текст и разбиваем его на части
        full_text = title.text.replace("\xa0", " ").strip()
        parts = full_text.split("ЄДРПОУ")

        if len(parts) == 2:
            company_name = parts[0].strip()
            edrpou = parts[1].strip()
            return company_name, edrpou

    return None, None


def process_html_file(file_path, combined_data):
    try:
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
        registration_date = get_registration_date(soup)  # '13.11.1996'
        authorized_person = get_authorized_person(
            soup
        )  # 'ЧЕРЕВАТИЙ СЕРГІЙ ВОЛОДИМИРОВИЧ'
        # 'МІНІСТЕРСТВО КУЛЬТУРИ ТА ІНФОРМАЦІЙНОЇ ПОЛІТИКИ УКРАЇНИ'
        founder = get_founder(soup)
        statutory_fund = get_statutory_fund(soup)  # '4 879 059,81 грн'
        bankruptcy_info = get_bankruptcy_info(soup)
        year, assets, liabilities, employees, profit, income = get_financial_info(soup)
        inn = get_inn(soup)
        title_mini, edrpo_new = get_mini_title(soup)
        if edrpo is None:
            edrpo = edrpo_new
        if title is None:
            return None
        all_data = {
            "title": title,
            "title_mini": title_mini,
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
            "registration_date": registration_date,
            "authorized_person": authorized_person,
            "founder": founder,
            "statutory_fund": statutory_fund,
            "bankruptcy_info": bankruptcy_info,
            "year": year,
            "assets": assets,
            "liabilities": liabilities,
            "employees": employees,
            "profit": profit,
            "income": income,
            "inn": inn,
        }
        return all_data
    except Exception as e:
        print(f"Ошибка при обработке файла {file_path}: {e}")
        return None


def get_bankruptcy_info(soup):
    # Находим элемент с заголовком "Процедура банкрутства"
    bankruptcy_element = soup.find(
        "div", class_="dr_value_title", string="Процедура банкрутства"
    )
    if not bankruptcy_element:
        return None

    # Проверяем наличие информации о банкротстве
    bankruptcy_info = bankruptcy_element.find_next("div", class_="dr_value_state")
    if bankruptcy_info:
        return bankruptcy_info.text.strip()

    # Если нет простого статуса, ищем детальную информацию
    detailed_info = []

    # Ищем дату начала
    date_element = bankruptcy_element.find_next(
        "div", class_="dr_value_subtitle", style=lambda x: x and "display: flex" in x
    )
    if date_element:
        detailed_info.append(date_element.text.strip())

    # Ищем описание
    description = bankruptcy_element.find_next("div", class_="dr_value_subtitle_2")
    if description:
        detailed_info.append(description.text.strip())

    # Ищем информацию о деле
    case_info = bankruptcy_element.find_next("div", string="Справа:")
    if case_info:
        detailed_info.append("Справа:")
        case_number = case_info.find_next("div", class_="dr_value")
        if case_number:
            detailed_info.append(case_number.text.strip())
            # Ищем дату дела
            case_date = case_number.find_next("div")
            if case_date:
                detailed_info.append(case_date.text.strip())

    # Если нашли детальную информацию, возвращаем её
    if detailed_info:
        return "\n".join(detailed_info)

    return None


def get_financial_info(soup):
    try:
        # Находим все div с классом dr_value_subtitle и их соответствующие значения
        values = {}
        for subtitle in soup.find_all("div", class_="dr_value_subtitle"):
            subtitle_text = subtitle.text.strip()
            if subtitle_text in [
                "Рік",
                "Активи",
                "Зобов'язання",
                "Кількість співробітників",
                "Чистий прибуток",
                "Дохід",
            ]:
                value = subtitle.find_next("div", class_="dr_value")
                if value:
                    values[subtitle_text] = (
                        value.text.strip()
                        .replace("\xa0", " ")
                        .replace(
                            "                                                            ",
                            "",
                        )
                        .replace("                            ", "")
                    )

        # Извлекаем значения в нужном порядке
        year = values.get("Рік")
        assets = values.get("Активи")
        liabilities = values.get("Зобов'язання")
        employees = values.get("Кількість співробітників")
        profit = values.get("Чистий прибуток")
        income = values.get("Дохід")

        return year, assets, liabilities, employees, profit, income

    except Exception as e:
        print(f"Ошибка при извлечении финансовой информации: {e}")
        return None, None, None, None, None, None


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
        # Предполагаем, что код идет первым в строке
        code = div.text.split()[0]
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
    print(f"Сохранено {len(results)} записей в файл {excel_file}")


def main():
    combined_data_file = current_directory / "combined_data.json"

    # Загрузка combined_data.json
    combined_data = load_combined_data(combined_data_file)

    # Получаем список всех HTML файлов
    all_html_files = list(html_directory.glob("*.html"))
    total_files = len(all_html_files)
    print(f"Найдено {total_files} HTML файлов для обработки")

    results = []
    processed_count = 0

    # Используем ThreadPoolExecutor для многопоточной обработки
    # Задаем максимальное количество потоков - 10
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        # Создаем список задач
        future_to_file = {
            executor.submit(process_html_file, html_file, combined_data): html_file
            for html_file in all_html_files
        }

        # Обрабатываем результаты по мере их завершения
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                data = future.result()
                processed_count += 1

                # Показываем прогресс каждые 100 файлов
                if processed_count % 100 == 0 or processed_count == total_files:
                    print(
                        f"Обработано {processed_count}/{total_files} файлов ({processed_count/total_files*100:.1f}%)"
                    )

                if data:
                    results.append(data)
            except Exception as e:
                print(f"Ошибка при обработке файла {file}: {e}")

    print(
        f"Обработка завершена. Получено {len(results)} результатов из {total_files} файлов"
    )

    # Сохраняем результаты в Excel
    save_to_excel(results)
    print("Работа программы завершена")


if __name__ == "__main__":
    main()
