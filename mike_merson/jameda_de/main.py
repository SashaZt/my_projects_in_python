import json
import random
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import pgeocode
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from get_response import Get_Response
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed
from tqdm import tqdm

current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_pages_directory = current_directory / "html_files_pages"
html_files_directory = current_directory / "html_files"
configuration_directory = current_directory / "configuration"
data_directory.mkdir(parents=True, exist_ok=True)
html_files_pages_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
input_csv_file = data_directory / "city.csv"
csv_file_successful = data_directory / "identifier_successful.csv"
output_json_file = data_directory / "output.json"
file_proxy = configuration_directory / "roman.txt"


cookies = {
    "OptanonAlertBoxClosed": "2024-10-15T11:50:36.242Z",
    "GUEST_SESSION": "6OD7hnxbDELLy0cpBJ_735jrFNL8KkbOmScIvVl3mVs",
    "patient-insurance-data": "{%22id%22:%222%22}",
    "mixpanel-events": "{%22s%22:1729707579152%2C%22u%22:%22/meike-hutzenlaub/orthopaede-unfallchirurg-akupunkteur-chirotherapeut/aachen%22%2C%22p%22:%22profile_visit%22%2C%22r%22:%22%22}",
    "OptanonConsent": "isGpcEnabled=0&datestamp=Wed+Oct+23+2024+21%3A20%3A38+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202405.2.0&browserGpcFlag=0&isIABGlobal=false&consentId=5f445bf3-ea3f-4378-8595-e19c933c67be&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1&hosts=H10%3A1%2CH163%3A1%2CH66%3A1%2CH67%3A1%2CH70%3A1%2CH159%3A1%2CH164%3A1%2CH158%3A1%2CH78%3A1%2CH112%3A1%2CH79%3A1%2CH133%3A1%2CH81%3A1%2CH82%3A1%2CH85%3A1%2CH86%3A1%2CH217%3A1%2CH160%3A1%2CH87%3A1%2CH11%3A1%2CH38%3A1%2CH12%3A1%2CH89%3A1%2CH182%3A1%2CH14%3A1%2CH15%3A1%2CH93%3A1%2CH76%3A1%2CH94%3A1%2CH32%3A1%2CH96%3A1%2CH208%3A1%2CH34%3A1%2CH74%3A1&genVendors=&intType=1&geolocation=%3B&AwaitingReconsent=false",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "referer": "https://www.jameda.de/",
    "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
}


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "roman.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


# Функция для чтения городов из CSV файла
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["city"].tolist()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(5),
    retry=retry_if_exception_type(requests.RequestException),
)
def get_page_city():
    cities = read_cities_from_csv(input_csv_file)
    proxies = load_proxies()  # Загружаем список всех прокси
    timeout = 100

    cookies = {
        "OptanonAlertBoxClosed": "2024-10-15T11:50:36.242Z",
        "GUEST_SESSION": "6OD7hnxbDELLy0cpBJ_735jrFNL8KkbOmScIvVl3mVs",
        "patient-insurance-data": "{%22id%22:%222%22}",
        "mixpanel-events": "{%22s%22:1729707579152%2C%22u%22:%22/meike-hutzenlaub/orthopaede-unfallchirurg-akupunkteur-chirotherapeut/aachen%22%2C%22p%22:%22profile_visit%22%2C%22r%22:%22%22}",
        "OptanonConsent": "isGpcEnabled=0&datestamp=Wed+Oct+23+2024+21%3A20%3A38+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202405.2.0&browserGpcFlag=0&isIABGlobal=false&consentId=5f445bf3-ea3f-4378-8595-e19c933c67be&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1&hosts=H10%3A1%2CH163%3A1%2CH66%3A1%2CH67%3A1%2CH70%3A1%2CH159%3A1%2CH164%3A1%2CH158%3A1%2CH78%3A1%2CH112%3A1%2CH79%3A1%2CH133%3A1%2CH81%3A1%2CH82%3A1%2CH85%3A1%2CH86%3A1%2CH217%3A1%2CH160%3A1%2CH87%3A1%2CH11%3A1%2CH38%3A1%2CH12%3A1%2CH89%3A1%2CH182%3A1%2CH14%3A1%2CH15%3A1%2CH93%3A1%2CH76%3A1%2CH94%3A1%2CH32%3A1%2CH96%3A1%2CH208%3A1%2CH34%3A1%2CH74%3A1&genVendors=&intType=1&geolocation=%3B&AwaitingReconsent=false",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://www.jameda.de/",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    }
    for loc in cities:
        proxy = random.choice(proxies)  # Выбираем случайный прокси
        proxies_dict = {"http": proxy, "https": proxy}
        logger.info(loc)

        params = {
            "q": "",
            "loc": loc,
        }

        try:
            response_start = requests.get(
                "https://www.jameda.de/suchen",
                params=params,
                cookies=cookies,
                headers=headers,
                proxies=proxies_dict,
                timeout=timeout,
            )
        except Exception as e:
            logger.error(f"Ошибка при запросе для {loc}: {e}")
            continue

        if response_start.status_code:
            logger.info(response_start.status_code)

            content = response_start.text
            soup = BeautifulSoup(content, "lxml")

            # Инициализируем total_pages значением по умолчанию
            total_pages = 1

            page_items = soup.find_all("li", attrs={"class": "page-item"})
            for item in reversed(page_items):
                page_text = item.find("a").get_text(strip=True)
                if page_text.isdigit():  # Проверяем, является ли текст числом
                    total_pages = int(page_text)
                    break
            logger.info(f"Всего страниц {total_pages}")
            max_pages = min(total_pages, 500)  # Ограничиваем количество страниц до 500

            for pages in range(1, max_pages + 1):
                proxy = random.choice(proxies)  # Выбираем случайный прокси
                proxies_dict = {"http": proxy, "https": proxy}
                output_html_page_file = (
                    html_files_pages_directory / f"{loc}_0{pages}.html"
                )
                # Проверяем, существует ли файл
                if output_html_page_file.exists():
                    logger.info(
                        f"Файл {output_html_page_file} уже существует, пропускаем."
                    )
                    continue  # Переходим к следующей итерации цикла
                params = {
                    "q": "",
                    "loc": loc,
                    "page": pages,
                }
                try:

                    response = requests.get(
                        "https://www.jameda.de/suchen",
                        params=params,
                        cookies=cookies,
                        headers=headers,
                        proxies=proxies_dict,
                        timeout=timeout,
                    )
                    with open(output_html_page_file, "w", encoding="utf-8") as file:
                        file.write(response.text)
                    logger.info(f"Сохранил {loc}_0{pages}.html")
                except Exception as e:
                    logger.error(f"Ошибка при запросе для {loc}: {e}")
                    continue
        else:
            logger.error(response_start.status_code)


def get_html_doctor():
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    cookies = {
        "OptanonAlertBoxClosed": "2024-10-15T11:50:36.242Z",
        "GUEST_SESSION": "dWQSx0M2o97XnFG4IFg4HUzjdyy4W3kCJwYROOPApZw",
        "mixpanel-events": "{%22s%22:1729577806102%2C%22u%22:%22/suchen?q=&loc=Aachen%22%2C%22p%22:%22/search_results_visits_new%22%2C%22r%22:%22%22}",
        "OptanonConsent": "isGpcEnabled=0&datestamp=Tue+Oct+22+2024+09%3A28%3A09+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202405.2.0&browserGpcFlag=0&isIABGlobal=false&consentId=5f445bf3-ea3f-4378-8595-e19c933c67be&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1&hosts=H10%3A1%2CH163%3A1%2CH66%3A1%2CH67%3A1%2CH70%3A1%2CH159%3A1%2CH164%3A1%2CH158%3A1%2CH78%3A1%2CH112%3A1%2CH79%3A1%2CH133%3A1%2CH81%3A1%2CH82%3A1%2CH85%3A1%2CH86%3A1%2CH217%3A1%2CH160%3A1%2CH87%3A1%2CH11%3A1%2CH38%3A1%2CH12%3A1%2CH89%3A1%2CH182%3A1%2CH14%3A1%2CH15%3A1%2CH93%3A1%2CH76%3A1%2CH94%3A1%2CH32%3A1%2CH96%3A1%2CH208%3A1%2CH34%3A1%2CH74%3A1&genVendors=&intType=1&geolocation=%3B&AwaitingReconsent=false",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        # 'cookie': 'OptanonAlertBoxClosed=2024-10-15T11:50:36.242Z; GUEST_SESSION=dWQSx0M2o97XnFG4IFg4HUzjdyy4W3kCJwYROOPApZw; mixpanel-events={%22s%22:1729577806102%2C%22u%22:%22/suchen?q=&loc=Aachen%22%2C%22p%22:%22/search_results_visits_new%22%2C%22r%22:%22%22}; OptanonConsent=isGpcEnabled=0&datestamp=Tue+Oct+22+2024+09%3A28%3A09+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202405.2.0&browserGpcFlag=0&isIABGlobal=false&consentId=5f445bf3-ea3f-4378-8595-e19c933c67be&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1&hosts=H10%3A1%2CH163%3A1%2CH66%3A1%2CH67%3A1%2CH70%3A1%2CH159%3A1%2CH164%3A1%2CH158%3A1%2CH78%3A1%2CH112%3A1%2CH79%3A1%2CH133%3A1%2CH81%3A1%2CH82%3A1%2CH85%3A1%2CH86%3A1%2CH217%3A1%2CH160%3A1%2CH87%3A1%2CH11%3A1%2CH38%3A1%2CH12%3A1%2CH89%3A1%2CH182%3A1%2CH14%3A1%2CH15%3A1%2CH93%3A1%2CH76%3A1%2CH94%3A1%2CH32%3A1%2CH96%3A1%2CH208%3A1%2CH34%3A1%2CH74%3A1&genVendors=&intType=1&geolocation=%3B&AwaitingReconsent=false',
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://www.jameda.de/meike-hutzenlaub/orthopaede-unfallchirurg-akupunkteur-chirotherapeut/aachen",
        cookies=cookies,
        headers=headers,
        proxies=proxies_dict,
    )

    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open("proba_0.html", "w", encoding="utf-8") as file:
            file.write(response.text)
    logger.info(response.status_code)


# def parsing_page():
#     # Множество для хранения уникальных itm_value
#     all_data = []
#     # Пройтись по каждому HTML файлу в папке
#     for html_file in html_files_directory.glob("*.html"):
#         with html_file.open(encoding="utf-8") as file:
#             logger.info(html_file)
#             # Прочитать содержимое файла
#             content: str = file.read()
#             # Создать объект BeautifulSoup
#             phone_number = None
#             profile = None
#             img = None
#             doctor_specializations = None
#             rating = None
#             reviews = None
#             name = None
#             clinic_name = None
#             adress = None
#             description = None
#             accepted_insurances = None
#             services = None
#             soup = BeautifulSoup(content, "lxml")
#             div_element = soup.find("div", attrs={"class": "card bg-gray-100"})

#             if div_element:

#                 phone_number_tag = div_element.find("b")
#                 if phone_number_tag:
#                     phone_number = phone_number_tag.get_text(strip=True)
#                     phone_number = phone_number.replace(" ", "").replace("\n", "")
#                     phone_number = f"+49{phone_number}"

#             profile_raw = soup.find("span", attrs={"class": "badge bg-warning-light"})
#             if profile_raw:
#                 profile = profile_raw.get_text(strip=True)
#             img_div = soup.find(
#                 "div", attrs={"class": "media mb-1 pb-md-1 align-items-stretch"}
#             )
#             if img_div:
#                 img_a = img_div.find("a")
#                 if img_a:
#                     img_raw = img_a.get("href")
#                 else:
#                     img_raw = None  # или другое значение по умолчанию
#             else:
#                 img_raw = None  # или другое значение по умолчанию

#             img = f"https:{img_raw}"
#             doctor_specializations_raw = soup.find(
#                 "span", attrs={"data-test-id": "doctor-specializations"}
#             )
#             if doctor_specializations_raw:
#                 doctor_specializations = " ".join(
#                     doctor_specializations_raw.get_text(strip=True).split()
#                 )
#                 doctor_specializations = [
#                     spec.strip() for spec in doctor_specializations.split(",")
#                 ]
#             rating_raw = soup.find(
#                 "u",
#                 attrs={
#                     "class": "rating rating-lg unified-doctor-header-info__rating-text"
#                 },
#             )
#             if rating_raw:
#                 rating = rating_raw.get("data-score")
#                 reviews = (
#                     rating_raw.find("span")
#                     .get_text(strip=True)
#                     .replace(" Bewertungen", "")
#                 )
#             name_raw = soup.find("span", attrs={"itemprop": "name"})
#             if name_raw:
#                 name = name_raw.get_text(strip=True)
#             clinic_name_raw = soup.find("div", attrs={"data-test-id": "address-info"})
#             if clinic_name_raw:
#                 # Проверяем, что элемент "a" существует
#                 clinic_name_element = clinic_name_raw.find("a")
#                 if clinic_name_element:
#                     clinic_name = " ".join(
#                         clinic_name_element.get_text(strip=True).split()
#                     )
#                 else:
#                     clinic_name = None  # или другое значение по умолчанию

#                 # Проверяем, что элемент с адресом существует
#                 adress_raw = clinic_name_raw.find(
#                     "span", attrs={"itemprop": "streetAddress"}
#                 )
#                 if adress_raw:
#                     adress = " ".join(adress_raw.get_text(strip=True).split())
#                 else:
#                     adress = None  # или другое значение по умолчанию
#             description_section = soup.find("section", id="about-section")
#             if description_section:
#                 title_element = description_section.find(
#                     "h2", class_="h3 section-header mb-1-5"
#                 )
#                 title = title_element.get_text(strip=True) if title_element else ""

#                 herzlich_willkommen_element = description_section.find_all(
#                     "div", class_="about-description"
#                 )
#                 herzlich_willkommen_text = " ".join(
#                     [
#                         " ".join(herz.get_text(separator=" ", strip=True).split())
#                         for herz in herzlich_willkommen_element
#                     ]
#                 )

#                 description = {
#                     "title": title,
#                     "Herzlich willkommen": herzlich_willkommen_text,
#                 }
#             accepted_insurances_raw = soup.find(
#                 "div", attrs={"data-test-id": "insurance-info"}
#             )
#             if accepted_insurances_raw:
#                 accepted_insurances = accepted_insurances_raw.find_all(
#                     "a", class_="text-muted"
#                 )
#                 accepted_insurances = [
#                     link.get_text(strip=True) for link in accepted_insurances
#                 ]
#             # Извлечение информации о сервисах и их описаниях
#             services_section = soup.find("section", id="profile-pricing")
#             services = []
#             if services_section:
#                 service_elements = services_section.find_all(
#                     "div", attrs={"data-test-id": "profile-pricing-list-details"}
#                 )
#                 for service_element in service_elements:
#                     service_name_element = service_element.find_previous_sibling(
#                         "div", attrs={"data-test-id": "profile-pricing-list-element"}
#                     )
#                     service_name = (
#                         service_name_element.find(
#                             "p", itemprop="availableService"
#                         ).get_text(strip=True)
#                         if service_name_element
#                         else ""
#                     )

#                     service_description_element = service_element.find(
#                         "p",
#                         attrs={"data-test-id": "profile-pricing-element-description"},
#                     )
#                     service_description = (
#                         " ".join(
#                             service_description_element.get_text(strip=True).split()
#                         )
#                         if service_description_element
#                         else ""
#                     )

#                     if service_name and service_description:
#                         services.append([service_name, service_description])
#             opening_hours_element = soup.find(
#                 "div", attrs={"data-id": re.compile(r"^opening-hours-.*")}
#             )
#             opening_hours = []
#             if opening_hours_element:
#                 rows = opening_hours_element.find_all(
#                     "div", class_=re.compile(r"row pb-0-5.*")
#                 )
#                 days_map = {
#                     "Montag": 0,
#                     "Dienstag": 1,
#                     "Mittwoch": 2,
#                     "Donnerstag": 3,
#                     "Freitag": 4,
#                     "Samstag": 5,
#                     "Sonntag": 6,
#                 }
#                 for row in rows:
#                     day_name_element = row.find("div", class_="col-4 col-md-4")
#                     if day_name_element:
#                         day_name = day_name_element.get_text(strip=True)
#                         day = days_map.get(day_name)
#                         if day is not None:
#                             ranges = []
#                             time_elements = row.find_all("div", class_="col-4 col-md-3")
#                             for time_element in time_elements:
#                                 times = (
#                                     time_element.get_text(strip=True)
#                                     .replace(" ", "")
#                                     .replace("\n", "")
#                                     .split("-")
#                                 )
#                                 if len(times) == 2:
#                                     ranges.append([times[0], times[1]])
#                             opening_hours.append({"day": day, "ranges": ranges})
#             datas = {
#                 "phone_number": phone_number,
#                 "profile": profile,
#                 "img": img,
#                 "doctor_specializations": doctor_specializations,
#                 "rating": rating,
#                 "reviews": reviews,
#                 "name": name,
#                 "clinic_name": clinic_name,
#                 "adress": adress,
#                 "description": description,
#                 "accepted_insurances": accepted_insurances,
#                 "services": services,
#                 "opening_hours": opening_hours,
#             }
#             all_data.append(datas)

#     save_data_to_json(all_data)


# def normalize_address(address):
#     """
#     Приводит адрес к шаблону:
#     [Улица] [Номер дома][ДОП], [Почтовый индекс] [Город]
#     Удаляет районы и нормализует пробелы.
#     """
#     # Убираем лишние пробелы
#     address = address.strip()

#     # Шаблоны для различных частей адреса
#     street_pattern = re.compile(r"(.+?)\s+(\d+(-\d+)?[a-zA-Z]?)")  # Улица и номер дома
#     postal_city_pattern = re.compile(r"(\d{5})?\s*(.+)")  # Почтовый индекс и город

#     street = ""
#     house_number = ""
#     postal_code = ""
#     city = ""

#     # Разбиваем адрес на части
#     parts = [part.strip() for part in address.split(",")]

#     # Ищем улицу и номер дома
#     street_match = street_pattern.match(parts[0])
#     if street_match:
#         street = street_match.group(1).strip()
#         house_number = street_match.group(2).strip()

#     # Обрабатываем оставшиеся части адреса
#     for part in parts[1:]:
#         if re.match(r"\d{5}", part):  # Почтовый индекс
#             postal_code = part
#         elif postal_code == "":  # Если почтовый индекс еще не найден
#             city = part

#     # Формируем адрес с нормализованными пробелами
#     normalized = f"{street} {house_number}, {postal_code} {city}".strip()
#     normalized = re.sub(r"\s+", " ", normalized)  # Удаляем лишние пробелы
#     normalized = re.sub(
#         r",\s+", ", ", normalized
#     )  # Убедимся, что после запятой ровно один пробел

#     return normalized


def validate_address(address):
    """
    Проверяет корректность адреса: улицы, почтового индекса и города.
    """
    # logger.info(f"Проверяем адрес: {address}")

    # Разбиваем адрес на части
    parts = [part.strip() for part in address.split(",")]
    if len(parts) < 2:
        return address  # Возвращаем оригинальный адрес, если не хватает частей

    # Ищем улицу и номер дома
    street = parts[0]

    # Ищем почтовый индекс и город (последние две части)
    postal_code = None
    city = None

    for part in parts[1:]:
        if re.match(r"^\d{5}$", part):  # Проверяем, является ли часть почтовым индексом
            postal_code = part
        else:
            city = part if not postal_code else f"{city} {part}"

    # Если нет почтового индекса или города, возвращаем адрес без изменений
    if not postal_code or not city:
        # logger.warning("Почтовый индекс или город отсутствует.")
        return address

    # Проверяем почтовый индекс и город через pgeocode
    nomi = pgeocode.Nominatim("de")  # Для Германии
    location = nomi.query_postal_code(postal_code)

    if location is None or not isinstance(location.place_name, str):
        logger.warning(f"Почтовый индекс {postal_code} не найден в базе данных.")
        return address  # Возвращаем оригинальный адрес, если индекс некорректен

    if city.lower() not in location.place_name.lower():
        logger.warning(
            f"Город {city} не соответствует почтовому индексу {postal_code}."
        )
        return address  # Возвращаем оригинальный адрес при несоответствии города

    # Если все проверки пройдены, возвращаем нормализованный адрес
    normalized_address = (
        f"{street}, {postal_code}, {city.split()[-1]}"  # Убираем район, если есть
    )
    logger.info(f"Адрес корректный: {normalized_address}")
    return normalized_address


def parsing_page(html_file):
    # Прочитать содержимое файла
    with html_file.open(encoding="utf-8") as file:
        # logger.info(html_file)
        content = file.read()

    # Создать объект BeautifulSoup
    soup = BeautifulSoup(content, "lxml")
    (
        phone_number,
        profile,
        img,
        doctor_specializations,
        rating,
        reviews,
        name,
        url_doctor,
    ) = (
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    clinic_name, address, description, accepted_insurances, services = (
        None,
        None,
        None,
        None,
        [],
    )

    profile_raw = soup.find("span", attrs={"class": "badge bg-warning-light"})
    if profile_raw:
        profile = profile_raw.get_text(strip=True)

    img_div = soup.find(
        "div", attrs={"class": "media mb-1 pb-md-1 align-items-stretch"}
    )
    img_raw = img_div.find("a").get("href") if img_div and img_div.find("a") else None
    img = f"https:{img_raw}" if img_raw and "amazonaws.com" in img_raw else None

    doctor_specializations_raw = soup.find(
        "span", attrs={"data-test-id": "doctor-specializations"}
    )
    if doctor_specializations_raw:
        doctor_specializations = [
            spec.strip()
            for spec in doctor_specializations_raw.get_text(strip=True).split(",")
        ]

    rating_raw = soup.find(
        "u", attrs={"class": "rating rating-lg unified-doctor-header-info__rating-text"}
    )
    if rating_raw:
        rating = rating_raw.get("data-score")
        reviews_span = rating_raw.find("span")
        if reviews_span:
            reviews = reviews_span.get_text(strip=True).replace(" Bewertungen", "")

    name_raw = soup.find("span", attrs={"itemprop": "name"})
    if name_raw:
        name = name_raw.get_text(strip=True)

    description_section = soup.find("section", id="about-section")
    if description_section:
        title_element = description_section.find(
            "h2", class_="h3 section-header mb-1-5"
        )
        title = title_element.get_text(strip=True) if title_element else ""
        herzlich_willkommen_element = description_section.find_all(
            "div", class_="about-description"
        )
        herzlich_willkommen_text = " ".join(
            [
                herz.get_text(separator=" ", strip=True)
                for herz in herzlich_willkommen_element
            ]
        )
        description = {"title": title, "Herzlich willkommen": herzlich_willkommen_text}

    accepted_insurances_raw = soup.find("div", attrs={"data-test-id": "insurance-info"})
    if accepted_insurances_raw:
        accepted_insurances = [
            link.get_text(strip=True)
            for link in accepted_insurances_raw.find_all("a", class_="text-muted")
        ]

    services_section = soup.find("section", id="profile-pricing")
    if services_section:
        service_elements = services_section.find_all(
            "div", attrs={"data-test-id": "profile-pricing-list-details"}
        )
        for service_element in service_elements:
            service_name_element = service_element.find_previous_sibling(
                "div", attrs={"data-test-id": "profile-pricing-list-element"}
            )
            if service_name_element:
                service_name = (
                    service_name_element.find(
                        "p", itemprop="availableService"
                    ).get_text(strip=True)
                    if service_name_element.find("p", itemprop="availableService")
                    else ""
                )
                service_description_element = service_element.find(
                    "p", attrs={"data-test-id": "profile-pricing-element-description"}
                )
                service_description = (
                    service_description_element.get_text(strip=True)
                    if service_description_element
                    else ""
                )
                if service_name and service_description:
                    services.append([service_name, service_description])

    all_clinic = soup.find("div", attrs={"data-id": "address-tabs-content"})
    polyclinics = []
    url_doctor_raw = soup.find("span", attrs={"itemprop": "url"})
    if url_doctor_raw:
        url_doctor = url_doctor_raw.get("content")

    if all_clinic:
        clinics = all_clinic.find_all("div", attrs={"data-id": "doctor-address-item"})

        for cl in clinics:
            lat = None
            lng = None
            offered_services = None
            lat_raw = cl.find("span", attrs={"itemprop": "latitude"})
            if lat_raw:
                lat = lat_raw.get("content")

            lng_raw = cl.find("span", attrs={"itemprop": "longitude"})
            if lng_raw:
                lng = lng_raw.get("content")
            gps = [{"lat": lat, "lng": lng}]
            offered_services_raw = cl.find("span", attrs={"class": "text-placeholder"})
            if offered_services_raw:
                offered_services = offered_services_raw.get_text(strip=True)

            phone_numbers = []
            div_elements = cl.find_all("div", attrs={"class": "card bg-gray-100"})

            if div_elements:
                for ph in div_elements:
                    phone_number_tag = ph.find("b")
                    if phone_number_tag:
                        phone_number = (
                            phone_number_tag.get_text(strip=True)
                            .replace(" ", "")
                            .replace("\n", "")
                        )
                        phone_number = f"+49{phone_number}"
                        phone_numbers.append(phone_number)

            clinic_name_raw = cl.find("div", attrs={"data-test-id": "address-info"})
            if clinic_name_raw:
                clinic_name_element = clinic_name_raw.find("a")
                clinic_name = (
                    clinic_name_element.get_text(strip=True)
                    if clinic_name_element
                    else None
                )
                address_raw = clinic_name_raw.find(
                    "span", attrs={"itemprop": "streetAddress"}
                )
                address = address_raw.get_text(strip=True) if address_raw else None
                address = validate_address(address)

            opening_hours_element = cl.find(
                "div", attrs={"data-id": re.compile(r"^opening-hours-.*")}
            )
            opening_hours = []
            if opening_hours_element:
                rows = opening_hours_element.find_all(
                    "div", class_=re.compile(r"row pb-0-5.*")
                )
                days_map = {
                    "Montag": 0,
                    "Dienstag": 1,
                    "Mittwoch": 2,
                    "Donnerstag": 3,
                    "Freitag": 4,
                    "Samstag": 5,
                    "Sonntag": 6,
                }
                for row in rows:
                    day_name_element = row.find("div", class_="col-4 col-md-4")
                    if day_name_element:
                        day_name = day_name_element.get_text(strip=True)
                        day = days_map.get(day_name)
                        if day is not None:
                            ranges = []
                            time_elements = row.find_all("div", class_="col-4 col-md-3")
                            for time_element in time_elements:
                                times = (
                                    time_element.get_text(strip=True)
                                    .replace(" ", "")
                                    .replace("\n", "")
                                    .replace("\t", "")
                                    .split("-")
                                )
                                if len(times) == 2:
                                    ranges.append([times[0], times[1]])
                            opening_hours.append({"day": day, "ranges": ranges})
            polyclinic = {
                "phone_number": phone_numbers,
                "clinic_name": clinic_name,
                "address": address,
                "services": services,
                "opening_hours": opening_hours,
                "gps": gps,
                "offered_services": offered_services,
            }
            polyclinics.append(polyclinic)

    return {
        "profile": profile,
        "url_doctor": url_doctor,
        "img": img,
        "doctor_specializations": doctor_specializations,
        "rating": rating,
        "reviews": reviews,
        "name": name,
        "polyclinics": polyclinics,
        "description": description,
        "accepted_insurances": accepted_insurances,
        "services": services,
    }


def save_data_to_json(datas):
    with open(output_json_file, "w", encoding="utf-8") as json_file:
        json.dump(datas, json_file, ensure_ascii=False, indent=4)


def get_url_in_pages():
    # Множество для хранения уникальных itm_value
    unique_itm_values = set()

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_files_pages_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content = file.read()
            # Создать объект BeautifulSoup
            soup = BeautifulSoup(content, "lxml")
            # Найти все <div> с классом 'str-quickview-button str-item-card__property-title'
            div_elements = soup.find_all("div", class_="pr-1")

            # Пройтись по каждому найденному элементу и извлечь itm из атрибута data-track
            for div in div_elements:
                data_track = div.find("a", attrs={"data-id": "address-context-cta"})

                if data_track:
                    # Преобразовать значение JSON обратно в словарь
                    href = data_track.get("href")

                    unique_itm_values.add(href)
    logger.info(len(unique_itm_values))
    # Создать DataFrame из списка URL
    df = pd.DataFrame(unique_itm_values, columns=["url"])

    # Записать DataFrame в CSV файл
    df.to_csv("unique_itm_urls.csv", index=False)


def pars_pagin():
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_files_pages_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content = file.read()
            # Создать объект BeautifulSoup
            soup = BeautifulSoup(content, "lxml")
            page_items = soup.find_all("li", attrs={"class": "page-item"})
            # Проходимся по элементам в обратном порядке
            for item in reversed(page_items):
                page_text = item.find("a").get_text(strip=True)
                if page_text.isdigit():  # Проверяем, является ли текст числом
                    total_pages = int(page_text)
                    logger.info(f"Всего страниц {total_pages}")
                    break
            else:
                # Если не нашли числовое значение, предполагаем, что всего одна страница
                total_pages = 1
                logger.info(f"Всего страниц {total_pages}")


def main(parallelism):
    # Получаем список всех HTML файлов
    html_files = list(html_files_directory.glob("*.html"))

    # Используем ThreadPoolExecutor и tqdm для отображения прогресса
    with ThreadPoolExecutor(max_workers=parallelism) as executor:
        all_data = list(
            tqdm(
                executor.map(parsing_page, html_files),
                total=len(html_files),
                desc="Обработка файлов",
            )
        )

    save_data_to_json(all_data)


if __name__ == "__main__":
    # get_page_city()
    # get_url_in_pages()
    # max_workers = 20
    # response_handler = Get_Response(
    #     max_workers,
    #     # base_url,
    #     cookies,
    #     headers,
    #     html_files_directory,
    #     csv_file_successful,
    #     output_csv_file,
    #     file_proxy,
    #     # url_sitemap,
    # )

    # # Запуск метода скачивания html файлов
    # response_handler.process_infox_file()

    parallelism = 50  # Укажите количество потоков
    main(parallelism)
