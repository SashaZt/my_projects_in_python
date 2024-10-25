import requests
import json
import re
from configuration.logger_setup import logger
import random
import pandas as pd
from pathlib import Path

current_directory = Path.cwd()
configuration_directory = current_directory / "configuration"
json_directory = current_directory / "json"
data_directory = current_directory / "data"

configuration_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)

file_proxy = configuration_directory / "roman.txt"
output_csv_file = data_directory / "output.csv"


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    with open(file_proxy, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


# Функция для чтения городов из CSV файла
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


def get_json_pages():
    timeout = 30
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}
    cookies = {
        "8020f80b5f22684beb6e2f5b559c57a9": "c5a427ee1d20c834b37ecb224ba52d87",
        "1686d7a14f465e6537467e88114cf7e8": "9009d01537a3658e432f2f7d1d1ffc69",
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "content-type": "application/json",
        # 'cookie': '8020f80b5f22684beb6e2f5b559c57a9=c5a427ee1d20c834b37ecb224ba52d87; 1686d7a14f465e6537467e88114cf7e8=9009d01537a3658e432f2f7d1d1ffc69',
        "dnt": "1",
        "origin": "https://purchasing.alberta.ca",
        "priority": "u=1, i",
        "referer": "https://purchasing.alberta.ca/search",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    }
    for offset in range(0, 5):
        json_data = {
            "query": "",
            "filter": {
                "solicitationNumber": "",
                "categories": [
                    {
                        "value": "CNST",
                        "selected": True,
                        "count": 0,
                    },
                ],
                "statuses": [
                    {
                        "value": "AWARD",
                        "selected": True,
                        "count": 0,
                    },
                ],
                "agreementTypes": [],
                "solicitationTypes": [],
                "opportunityTypes": [],
                "deliveryRegions": [],
                "deliveryRegion": "",
                "organizations": [],
                "unspsc": [],
                "postDateRange": "$$custom",
                "closeDateRange": "$$custom",
                "onlyBookmarked": False,
                "onlyInterestExpressed": False,
            },
            "limit": 100,
            "offset": offset,
            "sortOptions": [
                {
                    "field": "PostDateTime",
                    "direction": "desc",
                },
            ],
        }

        response = requests.post(
            "https://purchasing.alberta.ca/api/opportunity/search",
            cookies=cookies,
            headers=headers,
            json=json_data,
            timeout=timeout,
        )

        # Проверка кода ответа
        if response.status_code == 200:
            json_data = response.json()
            # filename = os.path.join(json_path, f"0.json")
            with open(f"proba_{offset}.json", "w", encoding="utf-8") as f:
                json.dump(
                    json_data, f, ensure_ascii=False, indent=4
                )  # Записываем в файл
        else:
            print(response.status_code)


def parisng_json_pages():
    # Обход всех JSON файлов в директории
    all_referenceNumber = []
    for json_file in json_directory.glob("*.json"):
        with json_file.open(encoding="utf-8") as file:
            # Прочитать содержимое JSON файла
            data = json.load(file)["values"]
        for json_data in data:
            referenceNumber = json_data["referenceNumber"]
            all_referenceNumber.append(referenceNumber)

    # Создаем DataFrame из списка с заголовком 'url'
    df = pd.DataFrame(all_referenceNumber, columns=["url"])

    # Записываем DataFrame в CSV файл
    df.to_csv(output_csv_file, index=False, encoding="utf-8")


def get_json_company():
    timeout = 60
    cities = read_cities_from_csv(output_csv_file)
    for loc in cities:
        year = loc.split("-")[-2]
        tender_id = loc.split("-")[-1]
        cookies = {
            "8020f80b5f22684beb6e2f5b559c57a9": "c5a427ee1d20c834b37ecb224ba52d87",
            "1686d7a14f465e6537467e88114cf7e8": "9009d01537a3658e432f2f7d1d1ffc69",
        }

        headers = {
            "accept": "application/json",
            "accept-language": "ru,en;q=0.9,uk;q=0.8",
            # 'cookie': '8020f80b5f22684beb6e2f5b559c57a9=c5a427ee1d20c834b37ecb224ba52d87; 1686d7a14f465e6537467e88114cf7e8=9009d01537a3658e432f2f7d1d1ffc69',
            "dnt": "1",
            "priority": "u=1, i",
            "referer": "https://purchasing.alberta.ca/posting/AB-2024-08660",
            "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        }
        json_company = json_directory / f"{year}_{tender_id}.json"
        if json_company.exists():
            logger.warning(f"Файл {json_company} уже существует, пропускаем.")
            continue  # Переходим к следующей итерации цикла
        response = requests.get(
            f"https://purchasing.alberta.ca/api/opportunity/{year}/{tender_id}",
            cookies=cookies,
            headers=headers,
            timeout=timeout,
        )

        # Проверка кода ответа
        if response.status_code == 200:
            json_data = response.json()

            with open(json_company, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            logger.info(json_company)
        else:
            print(response.status_code)


def paring_json_company():
    # invitation_to_bid = None
    # apc_reference = None
    # internal_reference = None
    # category = None
    # contracting_organization = None
    # organization_address = None
    # contact_person = None
    # method_of_contact = None
    # company_si = None
    # contact = None
    # person = None
    # email = None
    # phone = None
    # address = None
    # status = None
    # bid = None
    all_data = []
    for json_file in json_directory.glob("*.json"):
        with json_file.open(encoding="utf-8") as file:
            # Прочитать содержимое JSON файла
            data = json.load(file)
        # logger.warning(file)
        invitation_to_bid = data.get("opportunity", {}).get("shortTitle", None)
        apc_reference = data.get("opportunity", {}).get("referenceNumber", None)
        internal_reference = data.get("opportunity", {}).get("solicitationNumber", None)

        category_raw = data.get("opportunity", {}).get("categoryCode", None)
        category = "Construction" if category_raw == "CNST" else None

        contracting_organization_raw = (
            data.get("opportunity", {}).get("contactInformation", {}).get("city", None)
        )
        contracting_organization = (
            f"City of {contracting_organization_raw}"
            if contracting_organization_raw
            else None
        )

        addressLine1 = (
            data.get("opportunity", {})
            .get("contactInformation", {})
            .get("addressLine1", None)
        )
        province = (
            data.get("opportunity", {})
            .get("contactInformation", {})
            .get("province", None)
        )
        postalCode = (
            data.get("opportunity", {})
            .get("contactInformation", {})
            .get("postalCode", None)
        )
        organization_address = (
            f"{addressLine1} {contracting_organization_raw}, {province} {postalCode}"
            if addressLine1 and contracting_organization_raw and province and postalCode
            else None
        )

        firstName = (
            data.get("opportunity", {})
            .get("contactInformation", {})
            .get("firstName", None)
        )
        lastName = (
            data.get("opportunity", {})
            .get("contactInformation", {})
            .get("lastName", None)
        )
        title_name = (
            data.get("opportunity", {}).get("contactInformation", {}).get("title", None)
        )
        contact_person = (
            f"{firstName} {lastName} {title_name}"
            if firstName and lastName and title_name
            else None
        )

        method_of_contact = (
            data.get("opportunity", {})
            .get("contactInformation", {})
            .get("emailAddress", None)
        )
        datas_company = {
            "invitation_to_bid": invitation_to_bid,
            "apc_reference": apc_reference,
            "internal_reference": internal_reference,
            "category": category,
            "contracting_organization": contracting_organization,
            "organization_address": organization_address,
            "contact_person": contact_person,
            "method_of_contact": method_of_contact,
        }
        interestedSuppliers = data["interestedSuppliers"]
        for ins in interestedSuppliers:
            company_is = ins["businessName"]
            contact_person_is = ins["supplier"]["partnershipContactName"]
            email_is = ins["supplier"]["partnershipContactEmail"]
            phone_is = ins["supplier"]["partnershipContactPhoneNumber"]
            status_is = "Interested Suppliers"
            streetAddress_is = ins["physicalAddress"]["streetAddress"]
            city_is = ins["physicalAddress"]["city"]
            stateProvince_is = ins["physicalAddress"]["stateProvince"]
            datas_is = {
                "company_is": company_is,
                "contact_person_is": contact_person_is,
                "email_is": email_is,
                "phone_is": phone_is,
                "status_is": status_is,
            }
        bidders = data["bidders"]
        for bid in bidders:




        contact_person_si = None

        interested_suppliers = data.get("interestedSuppliers", [{}])
        email_si = (
            interested_suppliers[9]
            .get("supplier", {})
            .get("partnershipContactEmail", None)
            if len(interested_suppliers) > 9
            else None
        )
        phone_si = (
            interested_suppliers[9]
            .get("supplier", {})
            .get("partnershipContactPhoneNumber", None)
            if len(interested_suppliers) > 9
            else None
        )

        streetAddress = data.get("awards", [{}])[0].get("streetAddress", None)
        city_si = data.get("awards", [{}])[0].get("city", None)
        address_si = f"{streetAddress} {city_si}" if streetAddress and city_si else None

        status_si = "Awardee"
        bid_si = data.get("awards", [{}])[0].get("amount", None)

    # # Создание DataFrame и запись в файл Excel
    # df = pd.DataFrame(all_data)
    # df.to_excel("output.xlsx", index=False)


if __name__ == "__main__":
    # parisng_json_pages()
    # get_json_company()
    paring_json_company()
