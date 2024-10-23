import requests
import re
from configuration.logger_setup import logger
import random
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import json

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "roman.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def get_html():
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
        "referer": "https://www.jameda.de/suchen?q=&loc=Aachen",
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


def parsing_page():
    # Папка с HTML файлами
    html_folder = Path("html_files")

    # Множество для хранения уникальных itm_value

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_folder.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content: str = file.read()
            # Создать объект BeautifulSoup
            phone_number = None
            profile = None
            img = None
            doctor_specializations = None
            rating = None
            reviews = None
            name = None
            clinic_name = None
            adress = None
            description = None
            accepted_insurances = None
            services = None
            soup = BeautifulSoup(content, "lxml")
            div_element = soup.find("div", attrs={"class": "card bg-gray-100"})

            if div_element:

                phone_number_tag = div_element.find("b")
                if phone_number_tag:
                    phone_number = phone_number_tag.get_text(strip=True)
                    phone_number = phone_number.replace(" ", "").replace("\n", "")
                    phone_number = f"+49{phone_number}"

            profile_raw = soup.find("span", attrs={"class": "badge bg-warning-light"})
            if profile_raw:
                profile = profile_raw.get_text(strip=True)
            img_raw = (
                soup.find(
                    "div", attrs={"class": "media mb-1 pb-md-1 align-items-stretch"}
                )
                .find("a")
                .get("href")
            )

            img = f"https:{img_raw}"
            doctor_specializations_raw = soup.find(
                "span", attrs={"data-test-id": "doctor-specializations"}
            )
            if doctor_specializations_raw:
                doctor_specializations = " ".join(
                    doctor_specializations_raw.get_text(strip=True).split()
                )
                doctor_specializations = [
                    spec.strip() for spec in doctor_specializations.split(",")
                ]
            rating_raw = soup.find(
                "u",
                attrs={
                    "class": "rating rating-lg unified-doctor-header-info__rating-text"
                },
            )
            if rating_raw:
                rating = rating_raw.get("data-score")
                reviews = (
                    rating_raw.find("span")
                    .get_text(strip=True)
                    .replace(" Bewertungen", "")
                )
            name_raw = soup.find("span", attrs={"itemprop": "name"})
            if name_raw:
                name = name_raw.get_text(strip=True)
            clinic_name_raw = soup.find("div", attrs={"data-test-id": "address-info"})
            if clinic_name_raw:
                clinic_name = " ".join(
                    clinic_name_raw.find("a").get_text(strip=True).split()
                )
                adress_raw = clinic_name_raw.find(
                    "span", attrs={"itemprop": "streetAddress"}
                )
                adress = " ".join(adress_raw.get_text(strip=True).split())
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
                        " ".join(herz.get_text(separator=" ", strip=True).split())
                        for herz in herzlich_willkommen_element
                    ]
                )

                description = {
                    "title": title,
                    "Herzlich willkommen": herzlich_willkommen_text,
                }
            accepted_insurances_raw = soup.find(
                "div", attrs={"data-test-id": "insurance-info"}
            )
            if accepted_insurances_raw:
                accepted_insurances = accepted_insurances_raw.find_all(
                    "a", class_="text-muted"
                )
                accepted_insurances = [
                    link.get_text(strip=True) for link in accepted_insurances
                ]
                logger.info(accepted_insurances)
            # Извлечение информации о сервисах и их описаниях
            services_section = soup.find("section", id="profile-pricing")
            services = []
            if services_section:
                service_elements = services_section.find_all(
                    "div", attrs={"data-test-id": "profile-pricing-list-details"}
                )
                for service_element in service_elements:
                    service_name_element = service_element.find_previous_sibling(
                        "div", attrs={"data-test-id": "profile-pricing-list-element"}
                    )
                    service_name = (
                        service_name_element.find(
                            "p", itemprop="availableService"
                        ).get_text(strip=True)
                        if service_name_element
                        else ""
                    )

                    service_description_element = service_element.find(
                        "p",
                        attrs={"data-test-id": "profile-pricing-element-description"},
                    )
                    service_description = (
                        " ".join(
                            service_description_element.get_text(strip=True).split()
                        )
                        if service_description_element
                        else ""
                    )

                    if service_name and service_description:
                        services.append([service_name, service_description])

            datas = {
                "phone_number": phone_number,
                "profile": profile,
                "img": img,
                "doctor_specializations": doctor_specializations,
                "rating": rating,
                "reviews": reviews,
                "name": name,
                "clinic_name": clinic_name,
                "adress": adress,
                "description": description,
                "accepted_insurances": accepted_insurances,
                "services": services,
            }
            logger.info(datas)
            save_data_to_json(datas)


def save_data_to_json(datas, filename="output.json"):
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(datas, json_file, ensure_ascii=False, indent=4)


def get_url():
    # Папка с HTML файлами
    html_folder = Path("html_files")

    # Множество для хранения уникальных itm_value
    unique_itm_values = set()

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_folder.glob("*.html"):
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


if __name__ == "__main__":
    # get_html()
    parsing_page()
