import ast
import json
import re

import pandas as pd
from bs4 import BeautifulSoup


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

    # Словарь для хранения данных
    result_data = {"Awarded": [], "Submitted": [], "PlanTakers": []}

    # Регулярные выражения для поиска данных в JSON-like структурах
    awarded_pattern = re.compile(
        r'"CompanyName":"(.*?)","PrimaryContact":"(.*?)","Email":"(.*?)","Country":"(.*?)","ProvinceState":"(.*?)","Address1":"(.*?)","City":"(.*?)","PostalCode":"(.*?)"'
    )

    awarded_matches = awarded_pattern.findall(script_content)
    for match in awarded_matches:
        company_name, contact, email, country, province, address, city, postal_code = (
            match
        )
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

    # Аналогично для "Submitted" и "PlanTakers"
    submitted_pattern = re.compile(
        r'"CompanyName":"(.*?)","PrimaryContact":"(.*?)","Email":"(.*?)","Country":"(.*?)","ProvinceState":"(.*?)","Address1":"(.*?)","City":"(.*?)","PostalCode":"(.*?)"'
    )
    submitted_matches = submitted_pattern.findall(script_content)
    for match in submitted_matches:
        company_name, contact, email, country, province, address, city, postal_code = (
            match
        )
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
            }
        )

    plan_takers_pattern = re.compile(
        r'"CompanyName":"(.*?)","PrimaryContact":"(.*?)","Email":"(.*?)","Country":"(.*?)","ProvinceState":"(.*?)","Address1":"(.*?)","City":"(.*?)","PostalCode":"(.*?)"'
    )
    plan_takers_matches = plan_takers_pattern.findall(script_content)
    for match in plan_takers_matches:
        company_name, contact, email, country, province, address, city, postal_code = (
            match
        )
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


def write_exsls():
    # Read the JSON file
    with open("combined_output.json", "r", encoding="utf-8") as json_file:
        data = json.load(json_file)

    # Flatten the JSON data to extract and create rows for Awarded, Submitted, and PlanTakers
    rows = []

    # Function to add key-value pairs to rows
    def add_entries(section_name, items):
        for item in items:
            flattened_row = {"Section": section_name}
            flattened_row.update(item)
            rows.append(flattened_row)

    # Extract and flatten entries from each section
    for section in ["Awarded", "Submitted", "PlanTakers"]:
        if section in data:
            add_entries(section, data[section])

    # Create a DataFrame from the rows
    df = pd.DataFrame(rows)
    # Write the DataFrame to an Excel file
    output_excel_file = "combined_output_detailed.xlsx"
    df.to_excel(output_excel_file, index=False)


if __name__ == "__main__":
    # file_html = "zorra_4ca0de7b-08e8-438e-837f-554c2e2b8ebf.html"
    # data_script = parse_data_from_script(file_html)
    # data = parse_single_html_data(file_html)
    # # Объединение двух словарей в один
    # combined_data = (
    #     data.copy()
    # )  # Создаем копию словаря data, чтобы не изменять оригинал
    # combined_data.update(data_script)  # Добавляем содержимое словаря data_script

    # # Проверка объединенного словаря
    # # print(combined_data)

    # # Сохранение объединенного словаря в JSON файл
    # with open("combined_output.json", "w", encoding="utf-8") as json_file:
    #     json.dump(combined_data, json_file, ensure_ascii=False, indent=4)

    # print("Объединенные данные успешно сохранены в combined_output.json")
    write_exsls()
