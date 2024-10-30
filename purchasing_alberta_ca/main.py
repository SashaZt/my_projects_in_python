import requests
import json
import re
from configuration.logger_setup import logger
import random
import pandas as pd
import itertools
from pathlib import Path

current_directory = Path.cwd()
configuration_directory = current_directory / "configuration"
json_directory = current_directory / "json"
json_page_directory = current_directory / "json_page"
data_directory = current_directory / "data"
xlsx_directory = current_directory / "xlsx"

configuration_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
json_page_directory.mkdir(parents=True, exist_ok=True)
xlsx_directory.mkdir(parents=True, exist_ok=True)

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
    for offset in range(0, 7):
        json_data = {
            "query": '"engineering","build"',
            "filter": {
                "solicitationNumber": "",
                "categories": [],
                "statuses": [],
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
        file_page_file = json_page_directory / f"proba_{offset}.json"
        # Проверка кода ответа
        if response.status_code == 200:
            json_data = response.json()
            # filename = os.path.join(json_path, f"0.json")
            with open(file_page_file, "w", encoding="utf-8") as f:
                json.dump(
                    json_data, f, ensure_ascii=False, indent=4
                )  # Записываем в файл
        else:
            print(response.status_code)


def parisng_json_pages():
    # Обход всех JSON файлов в директории
    all_referenceNumber = []
    for json_file in json_page_directory.glob("*.json"):
        with json_file.open(encoding="utf-8") as file:
            # Прочитать содержимое JSON файла
            data = json.load(file)
        data_json = data["values"]
        for json_data in data_json:
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
            "1686d7a14f465e6537467e88114cf7e8": "cd7587b839180b3a48312edf364efdde",
            "8020f80b5f22684beb6e2f5b559c57a9": "31c0a0542b8c73b0d114a5826e376af7",
        }

        headers = {
            "accept": "application/json",
            "accept-language": "ru,en;q=0.9,uk;q=0.8",
            # 'cookie': '1686d7a14f465e6537467e88114cf7e8=cd7587b839180b3a48312edf364efdde; 8020f80b5f22684beb6e2f5b559c57a9=31c0a0542b8c73b0d114a5826e376af7',
            "dnt": "1",
            "priority": "u=1, i",
            "referer": "https://purchasing.alberta.ca/posting/AB-2024-04017",
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
        url = f"https://purchasing.alberta.ca/api/opportunity/public/{year}/{tender_id}"
        response = requests.get(
            url,
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
    # combined_rows = []
    for json_file in json_directory.glob("*.json"):
        with json_file.open(encoding="utf-8") as file:
            # Прочитать содержимое JSON файла
            data = json.load(file)
        logger.warning(file)

        invitation_to_bid = data.get("opportunity", {}).get("shortTitle", None)
        apc_reference = data.get("opportunity", {}).get("referenceNumber", None)
        internal_reference = data.get("opportunity", {}).get("solicitationNumber", None)

        category_raw = data.get("opportunity", {}).get("categoryCode", None)
        category = "Construction" if category_raw == "CNST" else None

        contracting_organization = (
            data.get("opportunity", {}).get("title", None).split(" - ")[0]
        )

        # contracting_organization = f"City of {contracting_organization_raw}"

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
            f"{addressLine1} {contracting_organization}, {province} {postalCode}"
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
        contact_person = f"{firstName} {lastName} {title_name}"

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
            "contact_person_company": contact_person,
            "method_of_contact": method_of_contact,
        }
        list_is_data = []
        for ins in data.get("interestedSuppliers", []):
            company_is = ins.get("businessName", None)
            contact_person_is = ins.get("supplier", {}).get(
                "partnershipContactName", None
            )
            email_is = ins.get("supplier", {}).get("partnershipContactEmail", None)
            phone_is = ins.get("supplier", {}).get(
                "partnershipContactPhoneNumber", None
            )
            status_is = "Interested Suppliers"
            streetAddress_is = ins.get("physicalAddress", {}).get("streetAddress", None)
            city_is = ins.get("physicalAddress", {}).get("city", None)
            stateProvince_is = ins.get("physicalAddress", {}).get("stateProvince", None)
            postalCode_is = ins.get("physicalAddress", {}).get("postalCode", None)
            physicalAddress_is = (
                f"{streetAddress_is} {city_is} {stateProvince_is} {postalCode_is}"
            )
            datas_is = {
                "company_is": company_is,
                "contact_person_is": contact_person_is,
                "email_is": email_is,
                "phone_is": phone_is,
                "status_is": status_is,
                "physicalAddress_is": physicalAddress_is,
            }
            list_is_data.append(datas_is)
        list_bd_data = []
        for bid in data.get("bidders", []):
            company_bid = bid.get("alternativeSupplierDisplayName", None)
            contact_person_bid = bid.get("contactName", None)
            email_bid = bid.get("contactEmail", None)
            phone_bid = bid.get("phoneNumber", None)
            status_bid = "Bidders list"
            bidAmounts = (
                bid.get("bidAmounts", [{}])[0].get("amount", None)
                if bid.get("bidAmounts")
                else None
            )

            streetAddress_bid = bid.get("physicalAddress", {}).get(
                "streetAddress", None
            )
            city_bid = bid.get("physicalAddress", {}).get("city", None)
            stateProvince_bid = bid.get("physicalAddress", {}).get(
                "stateProvince", None
            )
            postalCode_bid = bid.get("physicalAddress", {}).get("postalCode", None)
            physicalAddress_bid = (
                f"{streetAddress_bid} {city_bid} {stateProvince_bid} {postalCode_bid}"
            )
            datas_bid = {
                "company_bid": company_bid,
                "contact_person_bid": contact_person_bid,
                "email_bid": email_bid,
                "phone_bid": phone_bid,
                "status_bid": status_bid,
                "bidAmounts": bidAmounts,
                "physicalAddress_bid": physicalAddress_bid,
            }
            list_bd_data.append(datas_bid)
        list_aw_data = []
        for aw in data.get("awards", []):
            company_aw = aw.get("alternativeSupplierDisplayName", None)
            contact_person_aw = aw.get("contactName", None)
            status_aw = "Awardee"
            awAmounts = aw.get("amount", None)
            streetAddress_aw = aw.get("address", {}).get("streetAddress", None)
            streetAddress2_aw = aw.get("address", {}).get("streetAddress2", None)
            city_aw = aw.get("address", {}).get("city", None)
            stateProvince_aw = aw.get("address", {}).get("stateProvince", None)
            postalCode_aw = aw.get("address", {}).get("postalCode", None)
            physicalAddress_aw = f"{streetAddress2_aw}{streetAddress_aw} {city_aw} {stateProvince_aw} {postalCode_aw}"
            datas_aw = {
                "company_aw": company_aw,
                "contact_person_aw": contact_person_aw,
                "status_aw": status_aw,
                "awAmounts": awAmounts,
                "physicalAddress_aw": physicalAddress_aw,
            }
            list_aw_data.append(datas_aw)
            # Новый список для хранения всех строк
        # logger.info(len(list_is_data))
        # logger.info(len(list_bd_data))
        # logger.info(len(list_aw_data))
        # Новый список для хранения всех строк
        combined_rows = []

        # Комбинируем все возможные записи из всех списков

        for data_list in [list_is_data, list_bd_data, list_aw_data]:
            for data in data_list:
                # Копируем основной словарь, чтобы не изменять его напрямую
                new_row = datas_company.copy()

                # Объединяем значения общих ключей из разных словарей
                new_row["company"] = (
                    data.get("company_is")
                    or data.get("company_bid")
                    or data.get("company_aw")
                )
                new_row["contact_person"] = (
                    data.get("contact_person_is")
                    or data.get("contact_person_bid")
                    or data.get("contact_person_aw")
                )
                new_row["email"] = data.get("email_is") or data.get("email_bid")
                new_row["phone"] = data.get("phone_is") or data.get("phone_bid")
                new_row["status"] = (
                    data.get("status_is")
                    or data.get("status_bid")
                    or data.get("status_aw")
                )
                new_row["physicalAddress"] = (
                    data.get("physicalAddress_is")
                    or data.get("physicalAddress_bid")
                    or data.get("physicalAddress_aw")
                )
                new_row["amounts"] = data.get("bidAmounts") or data.get("awAmounts")

                # Добавляем остальные значения из словаря
                for key, value in data.items():
                    if key not in [
                        "company_is",
                        "company_bid",
                        "company_aw",
                        "contact_person_is",
                        "contact_person_bid",
                        "contact_person_aw",
                        "email_is",
                        "email_bid",
                        "phone_is",
                        "phone_bid",
                        "status_is",
                        "status_bid",
                        "status_aw",
                        "physicalAddress_is",
                        "physicalAddress_bid",
                        "physicalAddress_aw",
                        "bidAmounts",
                        "awAmounts",
                    ]:
                        new_row[key] = value

                # Добавляем новую строку в общий список
                combined_rows.append(new_row)
        output_xlsx_file = xlsx_directory / f"{apc_reference}.xlsx"
        # Создаем DataFrame из списка словарей
        df = pd.DataFrame(combined_rows)

        # Сохраняем DataFrame в Excel файл
        df.to_excel(output_xlsx_file, index=False)


def all_data():
    data_frames = []
    # Цикл по всем файлам с расширением .xlsx
    for xlsx_file in xlsx_directory.glob("*.xlsx"):
        df = pd.read_excel(xlsx_file)
        data_frames.append(df)

    # Объединение всех DataFrame в один
    combined_df = pd.concat(data_frames, ignore_index=True)

    # Сохранение результата в новый Excel файл
    combined_df.to_excel(current_directory / "combined_output.xlsx", index=False)


# # Создание DataFrame и запись в файл Excel
# df = pd.DataFrame(all_data)
# df.to_excel("output.xlsx", index=False)


if __name__ == "__main__":
    get_json_pages()
    parisng_json_pages()
    get_json_company()
    paring_json_company()
    all_data()
