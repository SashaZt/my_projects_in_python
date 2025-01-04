import json
import math
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests
from configuration.logger_setup import logger

# Путь к папкам
current_directory = Path.cwd()
json_tenders_diretory = current_directory / "json_tenders"
json_project = current_directory / "json_project"
json_page_diretory = current_directory / "json_page"
json_companydetails = current_directory / "json_companydetails"
xlsx_project = current_directory / "xlsx_project"
xlsx_CompanyDetails = current_directory / "xlsx_CompanyDetails"
xlsx_result = current_directory / "xlsx_result"
data_diretory = current_directory / "data"
configuration_directory = current_directory / "configuration"

xlsx_project.mkdir(exist_ok=True, parents=True)
xlsx_result.mkdir(exist_ok=True, parents=True)
xlsx_CompanyDetails.mkdir(exist_ok=True, parents=True)
json_page_diretory.mkdir(exist_ok=True, parents=True)
json_tenders_diretory.mkdir(exist_ok=True, parents=True)
json_project.mkdir(exist_ok=True, parents=True)
data_diretory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
file_proxy = configuration_directory / "roman.txt"
output_csv_file = data_diretory / "output.csv"


# Функция для чтения городов из CSV файла
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["id"].tolist()


def get_json_details():
    all_id = read_cities_from_csv(output_csv_file)
    cookies = {
        "messagesUtk": "a24cb7b40f42455191b94f513aa4b2c6",
        "ASP.NET_SessionId": "bal1jnkkkrw3c4oae45yxxs3",
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # 'Cookie': 'messagesUtk=a24cb7b40f42455191b94f513aa4b2c6; ASP.NET_SessionId=bal1jnkkkrw3c4oae45yxxs3',
        "DNT": "1",
        "Pragma": "no-cache",
        "Referer": "https://go.databid.com/NewDashboard/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    for pr_id in all_id:
        params = {
            "UserId": "106640",
            "ProjectID": pr_id,
        }
        file_name = json_tenders_diretory / f"{pr_id}_Details.json"
        if file_name.exists():
            continue
        try:
            # Выполняем запрос
            response = requests.get(
                "https://go.databid.com/newdashboard/api/api/ProjectDetails/GetProjectDetails",
                params=params,
                cookies=cookies,
                headers=headers,
                timeout=30,
            )
            # Проверяем статус ответа
            if response.status_code == 200:
                json_data = response.json()
                with open(file_name, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
                logger.info(f"Проект {pr_id} успешно сохранен в {file_name}.")
            else:
                logger.warning(
                    f"Ошибка {response.status_code} при обработке проекта {pr_id}."
                )
        except requests.exceptions.ReadTimeout:
            logger.error(f"ReadTimeout для проекта {pr_id}.")
        except requests.exceptions.SSLError as e:
            logger.error(f"SSLError для проекта {pr_id}: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"RequestException для проекта {pr_id}: {e}")
        except Exception as e:
            logger.error(f"Неизвестная ошибка для проекта {pr_id}: {e}")


def get_json_projectInvolvement():
    cookies = {
        "messagesUtk": "a24cb7b40f42455191b94f513aa4b2c6",
        "ASP.NET_SessionId": "bal1jnkkkrw3c4oae45yxxs3",
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Connection": "keep-alive",
        # 'Cookie': 'messagesUtk=a24cb7b40f42455191b94f513aa4b2c6; ASP.NET_SessionId=bal1jnkkkrw3c4oae45yxxs3',
        "DNT": "1",
        "Referer": "https://go.databid.com/NewDashboard/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    params = {
        "ProjectID": "280403",
    }

    response = requests.get(
        "https://go.databid.com/newdashboard/api/api/ProjectDetails/GetCompaniesDetails",
        params=params,
        cookies=cookies,
        headers=headers,
        timeout=30,
    )
    projectid = params["ProjectID"]
    json_data = response.json()
    with open(f"{projectid}_projectInvolvement.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл


def get_json_companydetails():
    cookies = {
        "messagesUtk": "a24cb7b40f42455191b94f513aa4b2c6",
        "ASP.NET_SessionId": "bal1jnkkkrw3c4oae45yxxs3",
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Connection": "keep-alive",
        # 'Cookie': 'messagesUtk=a24cb7b40f42455191b94f513aa4b2c6; ASP.NET_SessionId=bal1jnkkkrw3c4oae45yxxs3',
        "DNT": "1",
        "Referer": "https://go.databid.com/NewDashboard/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    params = {
        "UserId": "106640",
        "CompanyID": "31496",
    }

    response = requests.get(
        "https://go.databid.com/newdashboard/api/api/CompanyDetails/GetCompanyDetails",
        params=params,
        cookies=cookies,
        headers=headers,
        timeout=30,
    )
    companyid = params["CompanyID"]
    json_data = response.json()
    with open(f"{companyid}_CompanyDetails.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл


def get_page_json():

    cookies = {
        "messagesUtk": "a24cb7b40f42455191b94f513aa4b2c6",
        "ASP.NET_SessionId": "bal1jnkkkrw3c4oae45yxxs3",
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        # 'Cookie': 'messagesUtk=a24cb7b40f42455191b94f513aa4b2c6; ASP.NET_SessionId=bal1jnkkkrw3c4oae45yxxs3',
        "DNT": "1",
        "Origin": "https://go.databid.com",
        "Referer": "https://go.databid.com/NewDashboard/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    json_data = {
        "DueDateFrom": None,
        "DueDateTo": None,
        "EnteredDateFrom": None,
        "EnteredDateTo": None,
        "IndustryTypeID": ",16",
        "IndustrySubTypeID": ",91,87,92,86,89,219",
        "rptDow1List": "",
        "rptDow2List": "",
        "rptDow3List": "",
        "KeywordMatch": "primary",
        "RegionID": "",
        "CountyID": "",
        "rptStageList": "",
        "rptStageStatusList": "",
        "rptContractingMethodsList": "",
        "rptProjectClassList": "",
        "rptConstructionTypeList": "",
        "rptSectorList": "",
        "NewProjects": 0,
        "SavedSearchName": "",
        "gProjectSavedSearchID": 0,
        "SelectAllIndusty": False,
    }
    # for page in range(1218, 2418):
    for page in range(1, 27):
        file_name = json_page_diretory / f"page_0{page}.json"
        if file_name.exists():
            continue
        url = f"https://go.databid.com/newdashboard/api/api/AdvanceProjectSearch/addAdvanceProjectSearch?UserID=106640&ContactID=106726&RegionList=1,2,8,14,16,7&pageNo={page}&pageSize=100&SortOrder=0&SortDirection=1&SearchTxt=&ResultType=0&SavedSearchIDs=[object%20Object]"
        response = requests.post(
            url,
            cookies=cookies,
            headers=headers,
            json=json_data,
            timeout=60,
        )
        try:
            if response.status_code == 200:
                json_data = response.json()
                with open(file_name, "w", encoding="utf-8") as f:
                    json.dump(
                        json_data, f, ensure_ascii=False, indent=4
                    )  # Записываем в файл
                logger.info(file_name)
            else:
                break
        except requests.exceptions.ReadTimeout:
            logger.warning(f"Тайм-аут на странице {page}. Пропускаем.")
            break
        except requests.exceptions.SSLError as e:
            logger.warning(f"SSL ошибка на странице {page}: {e}. Пропускаем.")
            break
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ошибка запроса на странице {page}: {e}")
            break
        except Exception as e:
            logger.warning(f"Произошла неизвестная ошибка на странице {page}: {e}")
            break


def sanitize_value(value):
    """
    Очистить строку от недопустимых символов для Excel и HTML тегов.
    """
    if isinstance(value, str):
        # Удаляем все управляющие символы
        value = re.sub(r"[\x00-\x1F\x7F]", "", value)
        # Удаляем все HTML теги
        value = re.sub(r"<[^>]*>", "", value)
        # Удаляем избыточные пробелы
        value = re.sub(r"\s+", " ", value).strip()
    return value


def parsing_json_details():
    result = []
    for json_file in json_tenders_diretory.glob("*.json"):
        with json_file.open(encoding="utf-8") as file:
            data = json.load(file)
        # Извлекаем имя файла без расширения
        file_stem = json_file.stem  # '100000_Details'

        # Разделяем имя файла по символу "_"
        file_number = file_stem.split("_")[0]  # '100000'
        json_data = data["details"][0]
        bidDueToCustomerID = json_data.get("bidDueToCustomerID", None)
        bidDueToCustomerName = json_data.get("bidDueToCustomerName", None)
        projectseqno = json_data.get("projectSeqNo", None)
        projectdateno = json_data.get("projectDateNo", None)
        databid_id = f"{projectseqno}{projectdateno}"
        industry = json_data.get("industryName", None)
        project_bid_no = json_data.get("projectBidNo", None)
        project_class = json_data.get("projectClassName", None)
        projectstreet = json_data.get("projectStreet", None)
        projectcity = json_data.get("projectCity", None)
        statecode = json_data.get("stateCode", None)
        countyname = json_data.get("countyName", None)
        countryname = json_data.get("countryName", None)
        project_location = (
            f"{projectstreet},{projectcity}{statecode},{countyname},{countryname}"
        )
        sector = json_data.get("projectGroupName", None)
        stagename = json_data.get("stageName", None)
        contractingmethodname = json_data.get("contractingMethodName", None)

        stage = f"{stagename} - {contractingmethodname}"
        trade = json_data.get("tradeName", None)
        additionalInfo = json_data.get("additionalInfo", None)
        detailOfServices = json_data.get("detailOfServices", None)
        docProviderCustomerName = json_data.get("docProviderCustomerName", None)
        try:
            json_data_dow = data.get("dow", [])
            if json_data_dow:  # Проверяем, что "dow" существует и не пуст
                json_data_dow = json_data_dow[
                    0
                ]  # Получаем первый элемент, если он есть
                dowLevelOneName = json_data_dow.get("dowLevelOneName", None)
                dows = json_data_dow.get("dows", None)
            else:
                dowLevelOneName = None
                dows = None
        except (IndexError, AttributeError, KeyError):
            # Обработка ошибки, если структура JSON неожиданная
            dowLevelOneName = None
            dows = None
        all_data_detalis = {
            "bidDueToCustomerID": bidDueToCustomerID,
            "bidDueToCustomerName": bidDueToCustomerName,
            "tender_id": file_number,
            "databid_id": sanitize_value(databid_id),
            "industry": sanitize_value(industry),
            "project_bid_no": sanitize_value(project_bid_no),
            "project_class": sanitize_value(project_class),
            "project_location": sanitize_value(project_location),
            "sector": sanitize_value(sector),
            "stagename": sanitize_value(stage),
            "trade": sanitize_value(trade),
            "additionalInfo": sanitize_value(additionalInfo),
            "detailOfServices": sanitize_value(detailOfServices),
            "docProviderCustomerName": sanitize_value(docProviderCustomerName),
            "dowLevelOneName": sanitize_value(dowLevelOneName),
            "dows": sanitize_value(dows),
        }
        result.append(all_data_detalis)
    return result
    output_xlsx_file = current_directory / "tenders.xlsx"
    df = pd.DataFrame(result)

    # Сохраняем DataFrame в Excel файл
    df.to_excel(output_xlsx_file, index=False)


def parsing_json_project():

    for json_file in json_project.glob("*.json"):
        with json_file.open(encoding="utf-8") as file:
            data = json.load(file)
        result = []
        file_stem = json_file.stem  # '100000_Details'

        # Разделяем имя файла по символу "_"
        file_number = file_stem.split("_")[0]  # '100000'
        output_xlsx_file = xlsx_project / f"{file_number}.xlsx"
        # with open("10001_ProjectID.json", encoding="utf-8") as file:
        #     # Прочитать содержимое JSON файла
        #     data = json.load(file)
        try:
            projectinvolvement = data["projectInvolvement"][0]
        except:
            logger.info(json_file)

        prIn_companyID = projectinvolvement.get("companyID", None)
        prIn_role = projectinvolvement.get("role", None)
        prIn_projectContactID = projectinvolvement.get("projectContactID", None)
        prIn_location = projectinvolvement.get("location", None)
        prIn_phone = projectinvolvement.get("phone", None)
        prIn_fax = projectinvolvement.get("fax", None)
        prIn_customername = projectinvolvement.get("customerName", None)
        bidders = data["bidder"]
        results = data["results"]
        awards = data["awards"]
        # Проверяем наличие ключа "bidder"
        # Извлекаем нужные поля
        extracted_data = {
            "projectInvolvement": [
                {
                    "prIn_companyID": prIn_companyID,
                    "prIn_role": prIn_role,
                    "prIn_projectContactID": prIn_projectContactID,
                    "prIn_location": prIn_location,
                    "prIn_phone": prIn_phone,
                    "prIn_fax": prIn_fax,
                    "prIn_customername": prIn_customername,
                }
            ],
            "bidder": [
                {
                    "bidder_companyID": bidder.get("companyID", None),
                    "bidder_role": bidder.get("role", None),
                    "bidder_projectContactID": bidder.get("projectContactID", None),
                    "bidder_location": bidder.get("location", None),
                    "bidder_phone": bidder.get("phone", None),
                    "bidder_fax": bidder.get("fax", None),
                    "bidder_locationNamer": bidder.get("locationName", None),
                    "bidder_customerName": bidder.get("customerName", None),
                }
                for bidder in bidders
            ],
            "results": [
                {
                    "result_companyID": result.get("companyID", None),
                    "result_role": result.get("role", None),
                    "result_projectContactID": result.get("projectContactID", None),
                    "result_amount": result.get("amount", None),
                    "result_location": result.get("location", None),
                    "result_phone": result.get("phone", None),
                    "result_fax": result.get("fax", None),
                    "result_locationName_result": result.get("locationName", None),
                    "result_customerName_result": result.get("customerName", None),
                }
                for result in results
            ],
            "awards": [
                {
                    "award_companyID": award.get("companyID", None),
                    "award_role": award.get("role", None),
                    "award_amount": award.get("amount", None),
                    "award_location": award.get("location", None),
                    "award_phone": award.get("phone", None),
                    "award_fax": award.get("fax", None),
                    "award_locationName_result": award.get("locationName", None),
                    "result_customerName_result": award.get("customerName", None),
                }
                for award in awards
            ],
        }
        result.append(extracted_data)
        # Повторяем данные
        project_involvement = extracted_data["projectInvolvement"][
            0
        ]  # Берем первый объект из projectInvolvement

        # Генерация строк для каждой секции
        bidder_rows = [project_involvement | bidder for bidder in data["bidder"]]
        results_rows = [project_involvement | result for result in data["results"]]
        awards_rows = [project_involvement | award for award in data["awards"]]

        # Объединяем все строки
        all_rows = bidder_rows + results_rows + awards_rows
        return all_rows
        logger.info(all_rows)
        # Создаем DataFrame
        df = pd.DataFrame(all_rows)

        df.to_excel(output_xlsx_file, index=False)


def parsing_json_page():
    # Обход всех JSON файлов в директории
    all_projectid = []
    for json_file in json_page_diretory.glob("*.json"):
        with json_file.open(encoding="utf-8") as file:
            # Прочитать содержимое JSON файла
            data = json.load(file)
        for json_data in data:

            projectid = json_data["projectID"]
            all_projectid.append(projectid)

    # Создаем DataFrame из списка с заголовком 'url'
    df = pd.DataFrame(all_projectid, columns=["id"])

    # Записываем DataFrame в CSV файл
    df.to_csv(output_csv_file, index=False, encoding="utf-8")


# def merge_xlsx():

#     # Список для хранения данных из всех файлов
#     all_data = []

#     # Проход по всем файлам Excel в директории
#     for file in xlsx_result.glob("*.xlsx"):
#         try:
#             # Чтение данных из файла Excel
#             df = pd.read_excel(file)
#             all_data.append(df)
#             logger.info(f"Файл {file.name} успешно добавлен.")
#         except Exception as e:
#             logger.error(f"Ошибка при обработке файла {file.name}: {e}")

#     # Объединение всех данных в один DataFrame
#     merged_data = pd.concat(all_data, ignore_index=True)

#     # Определяем количество частей
#     num_parts = 10
#     part_size = len(merged_data) // num_parts

#     logger.info(
#         f"Общее количество строк: {len(merged_data)}, делим на {num_parts} частей по {part_size} строк."
#     )

#     # Разделение и сохранение данных
#     for i in range(num_parts):
#         start_row = i * part_size
#         end_row = (i + 1) * part_size if i < num_parts - 1 else len(merged_data)
#         part_data = merged_data.iloc[start_row:end_row]

#         # Генерируем имя файла
#         output_file = xlsx_project / f"merged_xlsx_project{i + 1}.xlsx"


#         # Сохраняем часть данных
#         part_data.to_excel(output_file, index=False)
#         logger.info(f"Часть {i + 1} данных сохранена в: {output_file}")
def merge_xlsx():

    # Список всех файлов Excel
    all_files = list(xlsx_result.glob("*.xlsx"))
    total_files = len(all_files)

    # Делим список файлов на 10 частей
    num_parts = 10
    files_per_part = total_files // num_parts
    logger.info(
        f"Всего файлов: {total_files}. Обрабатываем в {num_parts} частях, по {files_per_part} файлов в каждой."
    )

    for i in range(num_parts):
        # Определяем диапазон файлов для текущей части
        start_file = i * files_per_part
        end_file = (i + 1) * files_per_part if i < num_parts - 1 else total_files
        part_files = all_files[start_file:end_file]

        # Список для хранения данных текущей части
        part_data = []

        for file in part_files:
            try:
                # Чтение данных из файла Excel
                df = pd.read_excel(file)
                part_data.append(df)
                logger.info(f"Файл {file.name} успешно обработан.")
            except Exception as e:
                logger.error(f"Ошибка при обработке файла {file.name}: {e}")

        # Объединяем данные текущей части
        if part_data:
            merged_part = pd.concat(part_data, ignore_index=True)

            # Сохраняем объединенные данные текущей части
            output_file = xlsx_project / f"merged_xlsx_part_{i + 1}.xlsx"
            merged_part.to_excel(output_file, index=False)
            logger.info(f"Часть {i + 1} сохранена в: {output_file}")
        else:
            logger.warning(f"Часть {i + 1} не содержит данных.")


# def parsing_json_companydetails():
#     with open("176_CompanyDetails.json", encoding="utf-8") as file:
#         # Прочитать содержимое JSON файла
#         data = json.load(file)

#     companyalldetails = data["companyAllDetails"][0]
#     customerName = companyalldetails.get("customerName", None)
#     website = companyalldetails.get("website", None)
#     locationName = companyalldetails.get("locationName", None)
#     address1 = companyalldetails.get("address1", None)
#     address2 = companyalldetails.get("address2", None)
#     city = companyalldetails.get("city", None)
#     state = companyalldetails.get("state", None)
#     zip_company = companyalldetails.get("zip", None)
#     phone = companyalldetails.get("phone", None)
#     fax = companyalldetails.get("fax", None)
#     email = companyalldetails.get("email", None)
#     email2 = companyalldetails.get("email2", None)
#     email3 = companyalldetails.get("email3", None)
#     countryName = companyalldetails.get("countryName", None)
#     countyName = companyalldetails.get("countyName", None)
#     createdByFullName = companyalldetails.get("createdByFullName", None)
#     modifiedByFullName = companyalldetails.get("modifiedByFullName", None)
#     latitude = companyalldetails.get("countryName", None)
#     longitude = companyalldetails.get("countryName", None)
#     companyContacts = data["companyContacts"]


def pr_company():
    # Загрузка JSON файла
    # with open("176_CompanyDetails.json", encoding="utf-8") as f:
    #     data = json.load(f)
    for json_file in json_companydetails.glob("*.json"):
        with json_file.open(encoding="utf-8") as file:
            data = json.load(file)
        file_stem = json_file.stem  # '100000_Details'

        # Разделяем имя файла по символу "_"
        file_number = file_stem.split("_")[0]  # '100000'
        output_xlsx_file = xlsx_CompanyDetails / f"{file_number}_CompanyDetails.xlsx"
        if output_xlsx_file.exists():
            continue
        company_all_details = pd.DataFrame(
            data.get("companyAllDetails", [{}])
        ).reset_index(drop=True)

        # Извлекаем данные companyContacts
        company_contacts = pd.DataFrame(data.get("companyContacts", [])).reset_index(
            drop=True
        )

        # Извлекаем данные companyTypes
        company_types = pd.DataFrame(data.get("companyTypes", [])).reset_index(
            drop=True
        )

        # Логируем столбцы
        logger.info(
            "company_all_details columns: %s", list(company_all_details.columns)
        )
        logger.info("company_contacts columns: %s", list(company_contacts.columns))
        logger.info("company_types columns: %s", list(company_types.columns))

        # Повторяем companyAllDetails для companyContacts
        if not company_contacts.empty:
            repeated_all_details_contacts = company_all_details.loc[
                company_all_details.index.repeat(len(company_contacts))
            ].reset_index(drop=True)
            combined_contacts = pd.concat(
                [repeated_all_details_contacts, company_contacts], axis=1
            )
        else:
            combined_contacts = company_all_details

        # Обрабатываем companyTypes
        if not company_types.empty:
            repeated_all_details_types = company_all_details.loc[
                company_all_details.index.repeat(len(company_types))
            ].reset_index(drop=True)
            combined_types = pd.concat(
                [repeated_all_details_types, company_types], axis=1
            )
        else:
            combined_types = pd.DataFrame()

        # Удаляем дублирующиеся столбцы
        combined_contacts = combined_contacts.loc[
            :, ~combined_contacts.columns.duplicated()
        ]
        combined_types = combined_types.loc[:, ~combined_types.columns.duplicated()]

        # Объединяем contacts и types
        if not combined_types.empty:
            # Сравнение и приведение структур
            for col in combined_contacts.columns:
                if col not in combined_types.columns:
                    combined_types[col] = None
            for col in combined_types.columns:
                if col not in combined_contacts.columns:
                    combined_contacts[col] = None

            # Проверяем, совпадают ли структуры
            logger.info(
                "Final combined_contacts columns: %s", list(combined_contacts.columns)
            )
            logger.info(
                "Final combined_types columns: %s", list(combined_types.columns)
            )

            # Объединяем все данные
            combined_data = pd.concat(
                [combined_contacts, combined_types], ignore_index=True
            ).reset_index(drop=True)
        else:
            combined_data = combined_contacts

        # Сохранение в Excel

        combined_data.to_excel(output_xlsx_file, index=False)
        logger.info(f"Файл сохранён: {output_xlsx_file}")


def matches_1_2():
    project_details = parsing_json_details()
    companies_details = parsing_json_project()
    # Сопоставление данных
    # Сопоставление данных

    matches = []
    for project in project_details:
        for company in companies_details:
            if project["bidDueToCustomerID"] == company["prIn_companyID"]:
                match = {
                    "tender_id": project["tender_id"],
                    "bidDueToCustomerName": project["bidDueToCustomerName"],
                    "company_name": company["customerName"],
                    "company_role": company[
                        "role"
                    ],  # Используем реальную роль компании
                    "project_location": project["project_location"],
                    "company_location": company["prIn_location"],
                }
                matches.append(match)

    # Создание DataFrame
    df = pd.DataFrame(matches)

    # Сохранение в Excel
    output_path = "matches_corrected.xlsx"
    df.to_excel(output_path, index=False)


# def matc():
#     # Загрузка данных из файлов
#     with open("281660_Details.json", "r") as f:
#         details_data = json.load(f)

# with open("281660_ProjectID.json", "r") as f:
#     project_data = json.load(f)

#     # Извлечение всех данных из "details"
#     details = details_data["details"][0]
#     tender_info = {"Project ID": details["projectID"]}
#     # Добавляем все возможные поля из "details"
#     for key, value in details.items():
#         tender_info[key] = value

#     # Обработка "dow"
#     dow_entries = []
#     for entry in details_data.get("dow", []):
#         dow_entry = {"Project ID": details["projectID"], "Section": "dow"}
#         # Добавляем все поля из записи dow
#         for key, value in entry.items():
#             dow_entry[key] = value
#         dow_entries.append(dow_entry)

#     # Функция для обработки секций из ProjectID
#     def process_section(data, section_name):
#         results = []
#         for entry in data.get(section_name, []):
#             result = {"Section": section_name, "Project ID": details["projectID"]}
#             # Добавляем все возможные поля из текущей записи
#             for key, value in entry.items():
#                 result[key] = value
#             results.append(result)
#         return results

#     # Обработка всех секций из ProjectID
#     sections = ["projectInvolvement", "bidder", "results", "awards"]
#     all_entries = []

#     for section in sections:
#         all_entries.extend(process_section(project_data, section))

#     # Добавляем данные из dow
#     all_entries.extend(dow_entries)

#     # Создание DataFrame для всех секций
#     entries_df = pd.DataFrame(all_entries)

#     # Добавление всей информации из "details" к каждой записи
#     tender_info_df = pd.DataFrame([tender_info] * len(entries_df))
#     final_df = pd.concat([tender_info_df, entries_df], axis=1)

#     # Сохранение в Excel
#     output_path = "full_combined_tender_data_with_dow.xlsx"
#     final_df.to_excel(output_path, index=False)


#     print(f"Файл успешно сохранен: {output_path}")
# #     return output_path
# def matc():
#     # Загрузка данных из файлов
#     with open("281660_Details.json", "r") as f:
#         details_data = json.load(f)

#     with open("281660_ProjectID.json", "r") as f:
#         project_data = json.load(f)

#     # Извлечение всех данных из "details"
#     details = details_data["details"][0]
#     tender_info = {"Project ID": details["projectID"]}
#     # Добавляем все возможные поля из "details"
#     for key, value in details.items():
#         tender_info[key] = value

#     # Обработка "dow"
#     dow_combined = {
#         "dowLevelOneID": ";".join(
#             str(entry["dowLevelOneID"]) for entry in details_data.get("dow", [])
#         ),
#         "dowLevelOneName": ";".join(
#             entry["dowLevelOneName"] for entry in details_data.get("dow", [])
#         ),
#         "dows": ";".join(entry["dows"] for entry in details_data.get("dow", [])),
#     }

#     # Функция для обработки секций из ProjectID
#     def process_section(data, section_name):
#         results = []
#         for entry in data.get(section_name, []):
#             result = {"Section": section_name, "Project ID": details["projectID"]}
#             # Добавляем все возможные поля из текущей записи
#             for key, value in entry.items():
#                 result[key] = value
#             results.append(result)
#         return results

#     # Обработка всех секций из ProjectID
#     sections = ["projectInvolvement", "bidder", "results", "awards"]
#     all_entries = []

#     for section in sections:
#         all_entries.extend(process_section(project_data, section))

#     # Создание DataFrame для всех секций
#     entries_df = pd.DataFrame(all_entries)

#     # Добавление всей информации из "details" и "dow" к каждой записи
#     tender_info_df = pd.DataFrame([tender_info] * len(entries_df))
#     dow_df = pd.DataFrame([dow_combined] * len(entries_df))
#     final_df = pd.concat([tender_info_df, dow_df, entries_df], axis=1)

#     # Сохранение в Excel
#     output_path = "full_combined_tender_data_with_dow.xlsx"
#     final_df.to_excel(output_path, index=False)

#     print(f"Файл успешно сохранен: {output_path}")
#     return output_path


def matc():
    # Перебираем файлы в директории "json_tenders_directory"
    for tender_file in os.listdir(json_tenders_diretory):
        if tender_file.endswith(".json"):
            # Извлечение идентификатора тендера из имени файла
            tender_id = tender_file.split("_")[0]  # Берем часть до первого "_"
            # logger.info(tender_id)
            # Путь к файлу тендера
            output_file = xlsx_result / f"{tender_id}_full_.xlsx"
            if output_file.exists():
                continue
            tender_file_path = os.path.join(json_tenders_diretory, tender_file)

            # Путь к соответствующему файлу в "json_project"
            project_file_name = f"{tender_id}_ProjectID.json"
            project_file_path = os.path.join(json_project, project_file_name)
            # logger.info(project_file_name)
            # Проверяем, существует ли соответствующий файл
            if not os.path.exists(project_file_path):
                logger.error(
                    f"Файл для тендера {tender_id} отсутствует в {json_tenders_diretory}"
                )
                continue
            # Загрузка данных из файлов
            with open(tender_file_path, "r", encoding="utf-8") as f:
                details_data = json.load(f)
            with open(project_file_path, "r", encoding="utf-8") as f:
                project_data = json.load(f)

            # Извлечение всех данных из "details"
            details = details_data["details"][0]
            tender_info = {"Project ID": details["projectID"]}
            # Добавляем все возможные поля из "details"
            for key, value in details.items():
                tender_info[key] = value

            # Обработка "dow"
            dow_combined = {
                "dowLevelOneID": ";".join(
                    str(entry["dowLevelOneID"]) for entry in details_data.get("dow", [])
                ),
                "dowLevelOneName": ";".join(
                    entry["dowLevelOneName"] for entry in details_data.get("dow", [])
                ),
                "dows": ";".join(
                    entry["dows"] for entry in details_data.get("dow", [])
                ),
            }

            # Функция для обработки секций из ProjectID
            def process_section(data, section_name):
                results = []
                for entry in data.get(section_name, []):
                    result = {
                        "Section": section_name,
                        "Project ID": details["projectID"],
                    }
                    # Добавляем все возможные поля из текущей записи
                    for key, value in entry.items():
                        result[key] = value
                    results.append(result)
                return results

            # Обработка всех секций из ProjectID
            sections = ["projectInvolvement", "bidder", "results", "awards"]
            all_entries = []

            for section in sections:
                all_entries.extend(process_section(project_data, section))

            # Создание DataFrame для всех секций
            entries_df = pd.DataFrame(all_entries)

            # Добавление всей информации из "details" и "dow" к каждой записи
            tender_info_df = pd.DataFrame([tender_info] * len(entries_df))
            dow_df = pd.DataFrame([dow_combined] * len(entries_df))
            final_df = pd.concat([tender_info_df, dow_df, entries_df], axis=1)

            # Сохранение в Excel
            output_file = xlsx_result / f"{tender_id}_full_.xlsx"
            final_df.to_excel(output_file, index=False)

            logger.info(f"Файл успешно сохранен: {output_file}")
            # return output_file


if __name__ == "__main__":
    # get_page_json()
    # parsing_json_page()
    # get_json_details()
    # while True:
    #     get_json_details()
    #     time.sleep(5)
    # get_json_details()
    # get_json_projectInvolvement()
    # get_json_companydetails()

    # parsing_json_details()
    # parsing_json_project()
    # matches_1_2()
    # matc()
    merge_xlsx()
    # parsing_json_page()
    # pr_company()
