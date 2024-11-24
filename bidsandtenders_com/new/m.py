import json
import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
data_directory = current_directory / "data"
json_directory = current_directory / "json"
xlsx_directory = current_directory / "xlsx"
configuration_directory = current_directory / "configuration"

xlsx_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

output_csv_file = data_directory / "output.csv"
csv_file_successful = data_directory / "identifier_successful.csv"

json_result = json_directory / "result.json"
edrpou_csv_file = data_directory / "edrpou.csv"


def parse_single_html_data(file_html):
    # Открытие и чтение HTML-файла
    with open(file_html, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")

    # Словарь для хранения данных
    result_data = {}

    # Парсинг первой таблицы (Bid Details)
    bid_details_table = soup.find("table", {"aria-label": "Bid Details"})
    if bid_details_table:
        for row in bid_details_table.find_all("tr"):
            th = row.find("th").get_text(strip=True).replace(":", "")
            td = row.find("td").get_text(strip=True)
            result_data[th] = td

    # # Парсинг второй таблицы (Submitted Bids)
    # submitted_bids = []
    # submitted_table = soup.find("div", {"id": "dgSubmitted_Container"})
    # if submitted_table:
    #     for row in submitted_table.find_all("div", class_="x-grid3-row"):
    #         company = row.find("div", class_="x-grid3-col-CompanyName").get_text(
    #             strip=True
    #         )
    #         contact = row.find("div", class_="x-grid3-col-Contact").get_text(
    #             strip=True, separator=" "
    #         )
    #         result = row.find("div", class_="x-grid3-col-VerifiedValue").get_text(
    #             strip=True
    #         )
    #         submitted_bids.append(
    #             {"Company": company, "Contact": contact, "Result": result}
    #         )
    # result_data["Submitted Bids"] = submitted_bids

    # # Парсинг третьей таблицы (Plan Takers)
    # plan_takers = []
    # plan_takers_table = soup.find("div", {"id": "dgPlanTakers_Container"})
    # if plan_takers_table:
    #     for row in plan_takers_table.find_all("div", class_="x-grid3-row"):
    #         company = row.find("div", class_="x-grid3-col-CompanyName").get_text(
    #             strip=True
    #         )
    #         contact = row.find("div", class_="x-grid3-col-Contact").get_text(
    #             strip=True, separator=" "
    #         )
    #         plan_takers.append({"Company": company, "Contact": contact})
    # result_data["Plan Takers"] = plan_takers

    return result_data


def parse_data_from_script(file_html):
    # Открытие и чтение HTML-файла
    with open(file_html, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")

    # Поиск тега <script> с требуемыми данными
    script_tag = soup.find("script", text=re.compile("Ext\.net\.ResourceMgr\.init"))
    if not script_tag:
        return None

    script_content = script_tag.string

    # Удаление ненужных частей строк, включая поле SubmissionName
    script_content = re.sub(r',"SubmissionName":".*?"', "", script_content)

    # Словарь для хранения данных
    result_data = {"Awarded": [], "Submitted": [], "PlanTakers": []}

    # Регулярные выражения для поиска данных в JSON-like структурах
    awarded_pattern = re.compile(
        r'"CompanyName":"(.*?)","PrimaryContact":"(.*?)","Email":"(.*?)","Country":"(.*?)","ProvinceState":"(.*?)","Address1":"(.*?)","City":"(.*?)","PostalCode":"(.*?)"'
    )

    awarded_matches = awarded_pattern.findall(script_content)
    awarded_set = set()
    for match in awarded_matches:
        company_name, contact, email, country, province, address, city, postal_code = (
            match
        )
        awarded_entry = (
            company_name,
            contact,
            email,
            country,
            province,
            address,
            city,
            postal_code,
        )
        if awarded_entry not in awarded_set:
            awarded_set.add(awarded_entry)
            result_data["Awarded"].append(
                {
                    "CompanyName": company_name,
                    "PrimaryContact": contact,
                    "Email": email,
                    "Country": country,
                    "ProvinceState": province,
                    "Address1": address,
                    "City": city,
                    "PostalCode": postal_code,
                }
            )

    # Аналогично для "Submitted" с дополнительным полем "VerifiedValue"
    submitted_pattern = re.compile(
        r'"CompanyName":"(.*?)","PrimaryContact":"(.*?)","Email":"(.*?)","Country":"(.*?)","ProvinceState":"(.*?)","Address1":"(.*?)","City":"(.*?)","PostalCode":"(.*?)","VerifiedValue":"(.*?)"'
    )
    submitted_matches = submitted_pattern.findall(script_content)
    submitted_set = set()
    for match in submitted_matches:
        (
            company_name,
            contact,
            email,
            country,
            province,
            address,
            city,
            postal_code,
            verified_value,
        ) = match
        submitted_entry = (
            company_name,
            contact,
            email,
            country,
            province,
            address,
            city,
            postal_code,
            verified_value,
        )
        if submitted_entry not in submitted_set:
            submitted_set.add(submitted_entry)
            result_data["Submitted"].append(
                {
                    "CompanyName": company_name,
                    "PrimaryContact": contact,
                    "Email": email,
                    "Country": country,
                    "ProvinceState": province,
                    "Address1": address,
                    "City": city,
                    "PostalCode": postal_code,
                    "VerifiedValue": verified_value,
                }
            )

    # Аналогично для "PlanTakers"
    plan_takers_pattern = re.compile(
        r'"CompanyName":"(.*?)","PrimaryContact":"(.*?)","Email":"(.*?)","Country":"(.*?)","ProvinceState":"(.*?)","Address1":"(.*?)","City":"(.*?)","PostalCode":"(.*?)"'
    )
    plan_takers_matches = plan_takers_pattern.findall(script_content)
    plan_takers_set = set()
    for match in plan_takers_matches:
        company_name, contact, email, country, province, address, city, postal_code = (
            match
        )
        plan_takers_entry = (
            company_name,
            contact,
            email,
            country,
            province,
            address,
            city,
            postal_code,
        )
        if plan_takers_entry not in plan_takers_set:
            plan_takers_set.add(plan_takers_entry)
            result_data["PlanTakers"].append(
                {
                    "CompanyName": company_name,
                    "PrimaryContact": contact,
                    "Email": email,
                    "Country": country,
                    "ProvinceState": province,
                    "Address1": address,
                    "City": city,
                    "PostalCode": postal_code,
                }
            )
    return result_data


# def write_exsls():
#     # Read the JSON file
#     with open("combined_output.json", "r", encoding="utf-8") as json_file:
#         data = json.load(json_file)

#     # Flatten the JSON data to extract and create rows for Awarded, Submitted, and PlanTakers
#     rows = []

#     # Function to add key-value pairs to rows
#     def add_entries(section_name, items):
#         for item in items:
#             flattened_row = {"Section": section_name}
#             flattened_row.update(item)
#             rows.append(flattened_row)

#     # Extract and flatten entries from each section
#     for section in ["Awarded", "Submitted", "PlanTakers"]:
#         if section in data:
#             add_entries(section, data[section])

#     # Create a DataFrame from the rows
#     df = pd.DataFrame(rows)
#     # Write the DataFrame to an Excel file
#     output_excel_file = "combined_output_detailed.xlsx"
#     df.to_excel(output_excel_file, index=False)


def write_exsls(json_result, xlsx_result):
    # Read the JSON file
    with open(json_result, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)

    # Flatten the JSON data to extract and create rows for Awarded, Submitted, and PlanTakers
    rows = []
    bid_info = extract_bid_info(json_result)

    # Function to add key-value pairs to rows
    def add_entries(section_name, items):
        for item in items:
            flattened_row = {"Section": section_name}
            flattened_row.update(bid_info)  # Add the bid information to each row
            flattened_row.update(item)
            rows.append(flattened_row)

    # Extract and flatten entries from each section
    for section in ["Awarded", "Submitted", "PlanTakers"]:
        if section in data:
            add_entries(section, data[section])

    # Create a DataFrame from the rows
    df = pd.DataFrame(rows)
    # Write the DataFrame to an Excel file
    output_excel_file = xlsx_result
    df.to_excel(output_excel_file, index=False)


def extract_bid_info(json_file_path):
    # Открытие и чтение JSON-файла
    with open(json_file_path, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)

    # Извлечение информации о ставке (bid_info)
    bid_info_keys = [
        "Bid Classification",
        "Bid Type",
        "Bid Number",
        "Bid Name",
        "Bid Status",
        "Bid Awarded Date",
        "Published Date",
        "Bid Closing Date",
        "Question Deadline",
        "Electronic Auctions",
        "Language for Bid Submissions",
        "Submission Type",
        "Submission Address",
        "Public Opening",
        "Description",
        # "Bid Document Access",
        "Categories",
    ]

    # Создание словаря с информацией о ставке
    bid_info = {key: data.get(key) for key in bid_info_keys}
    return bid_info


if __name__ == "__main__":

    for html_file in html_files_directory.glob("*.html"):
        file_name = html_file.stem
        xlsx_result = xlsx_directory / f"{file_name}.xlsx"
        json_result = json_directory / f"{file_name}.json"
        if xlsx_result.exists() and json_result.exists():
            continue
        data_script = parse_data_from_script(html_file)
        logger.info("Данные по скрипту полученно ")
        data = parse_single_html_data(html_file)
        logger.info("Данные с html полученно")
        # Объединение двух словарей в один
        combined_data = data.copy()
        combined_data.update(data_script)  # Добавляем содержимое словаря data_script

        with open(json_result, "w", encoding="utf-8") as json_file:
            json.dump(combined_data, json_file, ensure_ascii=False, indent=4)

        logger.info("Объединенные данные успешно сохранены в combined_output.json")
        write_exsls(json_result, xlsx_result)
