import json
import math
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
            if response.status_code == 200:
                response = requests.get(
                    "https://go.databid.com/newdashboard/api/api/ProjectDetails/GetProjectDetails",
                    params=params,
                    cookies=cookies,
                    headers=headers,
                    timeout=30,
                )
                json_data = response.json()
                with open(file_name, "w", encoding="utf-8") as f:
                    json.dump(
                        json_data, f, ensure_ascii=False, indent=4
                    )  # Записываем в файл
            else:
                break
        except requests.exceptions.ReadTimeout:
            break
        except requests.exceptions.SSLError as e:
            break
        except requests.exceptions.RequestException as e:
            break
        except Exception as e:
            break


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
        "IndustryTypeID": "",
        "IndustrySubTypeID": "",
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
    for page in range(2117, 2200):
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
        # with open("280718_ProjectID.json", encoding="utf-8") as file:
        #     # Прочитать содержимое JSON файла
        #     data = json.load(file)
        try:
            projectinvolvement = data["projectInvolvement"][0]
        except:
            logger.info(json_file)

        involvement_companyID = projectinvolvement.get("companyID", None)
        involvement_role = projectinvolvement.get("role", None)
        involvement_location = projectinvolvement.get("location", None)
        involvement_phone = projectinvolvement.get("phone", None)
        involvement_customername = projectinvolvement.get("customerName", None)
        bidders = data["bidder"]
        results = data["results"]
        awards = data["awards"]
        # Проверяем наличие ключа "bidder"
        # Извлекаем нужные поля
        extracted_data = {
            "projectInvolvement": [
                {
                    "involvement_companyID": involvement_companyID,
                    "involvement_role": involvement_role,
                    "involvement_location": involvement_location,
                    "involvement_phone": involvement_phone,
                    "involvement_customername": involvement_customername,
                }
            ],
            "bidder": [
                {
                    "bidder_role": bidder.get("role"),
                    "bidder_location": bidder.get("location"),
                    "bidder_phone": bidder.get("phone"),
                    "bidder_fax": bidder.get("fax"),
                    "bidder_locationNamer": bidder.get("locationName"),
                    "bidder_customerName": bidder.get("customerName"),
                }
                for bidder in bidders
            ],
            "results": [
                {
                    "result_companyID": result.get("companyID"),
                    "result_role": result.get("role"),
                    "result_amount": result.get("amount"),
                    "result_location": result.get("location"),
                    "result_phone": result.get("phone"),
                    "result_fax": result.get("fax"),
                    "result_locationName_result": result.get("locationName"),
                    "result_customerName_result": result.get("customerName"),
                }
                for result in results
            ],
            "awards": [
                {
                    "award_companyID": award.get("companyID"),
                    "award_role": award.get("role"),
                    "award_amount": award.get("amount"),
                    "award_location": award.get("location"),
                    "award_phone": award.get("phone"),
                    "award_fax": award.get("fax"),
                    "award_locationName_result": award.get("locationName"),
                    "result_customerName_result": award.get("customerName"),
                }
                for award in awards
            ],
        }
        result.append(extracted_data)
        # Преобразование в табли формат
        # Преобразование в табличный формат
        rows = []

        for entry in result:
            project_involvement = entry.get("projectInvolvement", [{}])[0]
            bidder = entry.get("bidder", [])
            results = entry.get("results", [])
            awards = entry.get("awards", [])

            max_len = max(len(bidder), len(results))

            for i in range(max_len):
                row = {}
                # Добавляем данные projectInvolvement
                row.update(
                    {
                        "involvement_companyID": project_involvement.get(
                            "involvement_companyID", ""
                        ),
                        "involvement_role": project_involvement.get(
                            "involvement_role", ""
                        ),
                        "involvement_location": project_involvement.get(
                            "involvement_location", ""
                        ),
                        "involvement_phone": project_involvement.get(
                            "involvement_phone", ""
                        ),
                        "involvement_customername": project_involvement.get(
                            "involvement_customername", ""
                        ),
                    }
                )

                # Добавляем данные bidder
                if i < len(bidder):
                    row.update(
                        {
                            "bidder_role": bidder[i].get("bidder_role", ""),
                            "bidder_location": bidder[i].get("bidder_location", ""),
                            "bidder_phone": bidder[i].get("bidder_phone", ""),
                            "bidder_fax": bidder[i].get("bidder_fax", ""),
                            "bidder_locationNamer": bidder[i].get(
                                "bidder_locationNamer", ""
                            ),
                            "bidder_customerName": bidder[i].get(
                                "bidder_customerName", ""
                            ),
                        }
                    )
                else:
                    row.update(
                        {
                            "bidder_role": "",
                            "bidder_location": "",
                            "bidder_phone": "",
                            "bidder_fax": "",
                            "bidder_locationNamer": "",
                            "bidder_customerName": "",
                        }
                    )

                # Добавляем данные results
                if i < len(results):
                    row.update(
                        {
                            "result_companyID": results[i].get("result_companyID", ""),
                            "result_role": results[i].get("result_role", ""),
                            "result_amount": results[i].get("result_amount", ""),
                            "result_location": results[i].get("result_location", ""),
                            "result_phone": results[i].get("result_phone", ""),
                            "result_fax": results[i].get("result_fax", ""),
                            "result_locationName_result": results[i].get(
                                "result_locationName_result", ""
                            ),
                            "result_customerName_result": results[i].get(
                                "result_customerName_result", ""
                            ),
                        }
                    )
                else:
                    row.update(
                        {
                            "result_companyID": "",
                            "result_role": "",
                            "result_amount": "",
                            "result_location": "",
                            "result_phone": "",
                            "result_fax": "",
                            "result_locationName_result": "",
                            "result_customerName_result": "",
                        }
                    )

                # Добавляем данные awards
                if i < len(awards):
                    row.update(
                        {
                            "award_companyID": awards[i].get("award_companyID", ""),
                            "award_role": awards[i].get("award_role", ""),
                            "award_amount": awards[i].get("award_amount", ""),
                            "award_location": awards[i].get("award_location", ""),
                            "award_phone": awards[i].get("award_phone", ""),
                            "award_fax": awards[i].get("award_fax", ""),
                            "award_locationName_result": awards[i].get(
                                "award_locationName_result", ""
                            ),
                            "result_customerName_result": awards[i].get(
                                "result_customerName_result", ""
                            ),
                        }
                    )
                else:
                    row.update(
                        {
                            "award_companyID": "",
                            "award_role": "",
                            "award_amount": "",
                            "award_location": "",
                            "award_phone": "",
                            "award_fax": "",
                            "award_locationName_result": "",
                            "result_customerName_result": "",
                        }
                    )

                rows.append(row)
        output_xlsx_file = xlsx_project / f"{file_number}.xlsx"
        # Создаем DataFrame
        df = pd.DataFrame(rows)

        # Сохраняем в Excel
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


def merge_xlsx():

    # Список для хранения данных из всех файлов
    all_data = []

    # Проход по всем файлам Excel в директории
    for file in xlsx_CompanyDetails.glob("*.xlsx"):
        try:
            # Чтение данных из файла Excel
            df = pd.read_excel(file)
            all_data.append(df)
            logger.info(f"Файл {file.name} успешно добавлен.")
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {file.name}: {e}")

    # Объединение всех данных в один DataFrame
    merged_data = pd.concat(all_data, ignore_index=True)

    # Определяем количество частей
    num_parts = 10
    part_size = len(merged_data) // num_parts

    logger.info(
        f"Общее количество строк: {len(merged_data)}, делим на {num_parts} частей по {part_size} строк."
    )

    # Разделение и сохранение данных
    for i in range(num_parts):
        start_row = i * part_size
        end_row = (i + 1) * part_size if i < num_parts - 1 else len(merged_data)
        part_data = merged_data.iloc[start_row:end_row]

        # Генерируем имя файла
        output_file = xlsx_result / f"merged_CompanyDetails{i + 1}.xlsx"

        # Сохраняем часть данных
        part_data.to_excel(output_file, index=False)
        logger.info(f"Часть {i + 1} данных сохранена в: {output_file}")


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


if __name__ == "__main__":
    # while True:
    # get_json_details()
    # time.sleep(10)
    # get_json_details()
    # get_json_projectInvolvement()
    # get_json_companydetails()

    # parsing_json_details()
    # parsing_json_project()
    merge_xlsx()
    # parsing_json_page()
    # pr_company()
