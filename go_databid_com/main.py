import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from configuration.logger_setup import logger

# Путь к папкам
current_directory = Path.cwd()
json_page_diretory = current_directory / "json_page"
configuration_directory = current_directory / "configuration"

json_page_diretory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
file_proxy = configuration_directory / "roman.txt"


# Загружаем прокси
def load_proxies():
    with open(file_proxy, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


proxies = load_proxies()


def get_json_details():
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

    params = {
        "UserId": "106640",
        "ProjectID": "280403",
    }

    response = requests.get(
        "https://go.databid.com/newdashboard/api/api/ProjectDetails/GetProjectDetails",
        params=params,
        cookies=cookies,
        headers=headers,
        timeout=30,
    )
    projectid = params["ProjectID"]
    json_data = response.json()
    with open(f"{projectid}_Details.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл


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
    with open(f"{companyid}_projectInvolvement.json", "w", encoding="utf-8") as f:
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
    for page in range(1, 2418):
        file_name = json_page_diretory / f"page_0{page}.json"
        if file_name.exists():
            continue
        url = f"https://go.databid.com/newdashboard/api/api/AdvanceProjectSearch/addAdvanceProjectSearch?UserID=106640&ContactID=106726&RegionList=1,2,8,14,16,7&pageNo={page}&pageSize=100&SortOrder=0&SortDirection=1&SearchTxt=&ResultType=0&SavedSearchIDs=[object%20Object]"
        response = requests.post(
            url,
            cookies=cookies,
            headers=headers,
            json=json_data,
            timeout=10,
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
            logger.error(f"Тайм-аут на странице {page}. Завершаем цикл.")
            break
        except Exception as e:
            logger.error(f"Произошла ошибка на странице {page}: {e}")
            break


def parsing_json_details():
    with open("280403_Details.json", encoding="utf-8") as file:
        # Прочитать содержимое JSON файла
        data = json.load(file)
    json_data = data["details"][0]
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
    all_data_detalis = {
        "databid_id": databid_id,
        "industry": industry,
        "project_bid_no": project_bid_no,
        "project_class": project_class,
        "project_location": project_location,
        "sector": sector,
        "stagename": stage,
        "trade": trade,
    }
    logger.info(all_data_detalis)


def parsing_json_project():
    with open("280403_projectInvolvement.json", encoding="utf-8") as file:
        # Прочитать содержимое JSON файла
        data = json.load(file)
    projectinvolvement = data["projectInvolvement"][0]

    projectinvolvement_role = projectinvolvement.get("role", None)
    projectinvolvement_location = projectinvolvement.get("location", None)
    projectinvolvement_phone = projectinvolvement.get("phone", None)
    projectinvolvement_customername = projectinvolvement.get("customerName", None)
    bidders = data["bidder"]
    all_data_project = {
        "projectInvolvement": [
            {
                "projectinvolvement_role": projectinvolvement_role,
                "projectinvolvement_location": projectinvolvement_location,
                "projectinvolvement_phone": projectinvolvement_phone,
                "projectinvolvement_customername": projectinvolvement_customername,
            }
        ]
    }
    # Проверяем наличие ключа "bidder"
    # Извлекаем нужные поля
    extracted_data = {
        "bidder": [
            {
                "role": bidder.get("role"),
                "location": bidder.get("location"),
                "phone": bidder.get("phone"),
                "fax": bidder.get("fax"),
                "locationName": bidder.get("locationName"),
                "customerName": bidder.get("customerName"),
            }
            for bidder in bidders
        ]
    }

    logger.info(all_data_project)


if __name__ == "__main__":
    # main()
    while True:
        get_page_json()
        time.sleep(10)
    # get_json_details()
    # get_json_projectInvolvement()
    # get_json_companydetails()

    # parsing_json_details()
    # parsing_json_project()
