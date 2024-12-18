import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

# Базовый URL для запроса sitemap
BASE_URL = "https://www.focus-gesundheit.de/sitemap/sitemap.gesundheit.xml"

current_directory = Path.cwd()
data_directory = current_directory / "data"
xml_directory = current_directory / "xml"
html_directory = current_directory / "html"
# json_directory = current_directory / "json"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(exist_ok=True, parents=True)
# json_directory.mkdir(exist_ok=True, parents=True)
xml_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

start_sitemap = xml_directory / "sitemap.xml"
output_csv = data_directory / "output.csv"
all_url_sitemap = data_directory / "sitemap.csv"


def fetch_sitemap_links():
    """
    Загружает основной файл sitemap и извлекает ссылки на подкарты.
    """
    response = requests.get(BASE_URL, timeout=30)
    if response.status_code != 200:
        raise Exception(f"Ошибка при загрузке {BASE_URL}: {response.status_code}")

    # Парсим XML и извлекаем ссылки на подкарты
    root = ET.fromstring(response.content)
    namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_links = [elem.text for elem in root.findall(".//ns:loc", namespaces)]
    return [link for link in sitemap_links if "sitemap.gesundheit.entries" in link]


def download_and_parse_sitemaps(sitemap_links):
    """
    Скачивает файлы sitemap и извлекает ссылки, содержащие "/arzt".
    """
    arzt_links = []

    for link in sitemap_links:
        filename = xml_directory / Path(link).name
        response = requests.get(link, timeout=30)
        if response.status_code != 200:
            print(f"Ошибка загрузки {link}: {response.status_code}")
            continue

        # Сохраняем локально
        with open(filename, "wb") as file:
            file.write(response.content)
        print(f"Файл {filename} успешно загружен.")

        # Парсим XML для извлечения ссылок
        root = ET.fromstring(response.content)
        namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [elem.text for elem in root.findall(".//ns:loc", namespaces)]
        arzt_links.extend([url for url in urls if "/arzt" in url])

    return arzt_links


def save_to_csv(urls, output_file):
    """
    Сохраняет ссылки в CSV файл.
    """
    df = pd.DataFrame(urls, columns=["url"])
    df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"Результаты успешно сохранены в {output_file}")


def main():
    # Шаг 1: Получение ссылок на подкарты
    sitemap_links = fetch_sitemap_links()
    logger.info(f"Найдено {len(sitemap_links)} подкарт.")

    # Шаг 2: Скачивание файлов sitemap и извлечение ссылок
    arzt_links = download_and_parse_sitemaps(sitemap_links)
    logger.info(f"Найдено {len(arzt_links)} ссылок, содержащих '/arzt'.")

    # Шаг 3: Сохранение результатов в CSV файл
    save_to_csv(arzt_links, output_csv)


# Функция для преобразования времени в нужный формат
def parse_opening_hours(soup):
    # Дни недели для сопоставления с индексами
    weekdays = [
        "Montag",
        "Dienstag",
        "Mittwoch",
        "Donnerstag",
        "Freitag",
        "Samstag",
        "Sonntag",
    ]
    opening_hours = []

    opening_hours_raw = soup.find("div", {"class": "opening-hours"})

    # Обработка и формирование данных
    day_hours = {
        day: [] for day in range(7)
    }  # Создаем словарь с пустыми диапазонами на все дни недели

    for div in opening_hours_raw.find_all("div"):
        text = div.text.strip()
        for idx, day in enumerate(weekdays):
            if day in text:
                time_ranges = text.split(": ", 1)[-1]  # Берём часть с временем
                ranges = []
                for time_range in time_ranges.split(", "):  # Если несколько диапазонов
                    start_end = time_range.split(" - ")
                    if len(start_end) == 2:
                        ranges.append(start_end)
                day_hours[idx] = ranges

    # Преобразуем в нужный формат
    for day, ranges in day_hours.items():
        opening_hours.append({"day": day, "ranges": ranges})

    return opening_hours


def format_phone_fax(number):
    if number and not number.startswith("+49"):
        return f"+49{number}"
    return number


# Функция для чтения городов из CSV файла
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


def extract_special_features(soup):
    """
    Извлекает текстовые значения из элемента с классом 'eq-tags eq-special-features'.

    Args:
        soup (BeautifulSoup): Объект парсинга HTML.

    Returns:
        list: Список текстовых значений.
    """
    # Находим элемент по классу
    container = soup.find("div", {"class": "eq-tags eq-special-features"})

    # Проверяем, найден ли элемент
    if container:
        # Извлекаем текст из всех span элементов внутри <div>
        features = [
            span.text.strip()
            for span in container.find_all("span")
            if span.text.strip()
        ]
        return features
    else:
        return []


def extract_service_titles(soup):
    """
    Извлекает текст из тегов <h4> внутри элементов с классом 'services-card'.

    Args:
        soup (BeautifulSoup): Объект парсинга HTML.

    Returns:
        list: Список текстовых значений из <h4>.
    """
    # Находим все элементы с классом "services-card" и берем из них <h4>
    service_titles = [h4.text.strip() for h4 in soup.select(".services-card h4")]
    return service_titles


def extract_about_text(soup):
    """
    Извлекает текст из тега <p> внутри элемента <section> с классом 'about'.

    Args:
        soup (BeautifulSoup): Объект парсинга HTML.

    Returns:
        str: Текст из тега <p> (или пустая строка, если элемент не найден).
    """
    # Находим элемент <section> с классом "about" и берем его <p>
    about_section = soup.find("section", {"class": "about"})
    if about_section:
        p_tag = about_section.find("p")
        if p_tag:
            return p_tag.text.strip()
    return ""


def extract_doctors_data(soup):
    """
    Извлекает данные о врачах из HTML и возвращает массив словарей.

    Args:
        soup (BeautifulSoup): Объект парсинга HTML.

    Returns:
        list: Список словарей с информацией о врачах.
    """
    doctors_data = []

    # Находим все карточки врачей
    doctor_cards = soup.find_all("div", class_="doctor-card")

    for card in doctor_cards:
        # Извлекаем имя врача
        name_tag = card.find("p", class_="name")
        name = name_tag.text.strip() if name_tag else ""

        # Извлекаем специальность врача (job)
        job_tag = card.find("p", class_="job")
        job = job_tag.text.strip() if job_tag else ""

        # Извлекаем специализации врача из "consultations"
        specializations = []
        consultations_section = card.find("div", class_="consultations")
        if consultations_section:
            specialization_tags = consultations_section.find_all("div", style=True)
            specializations = [spec.text.strip() for spec in specialization_tags]

        # Добавляем данные врача в список
        doctor_info = {
            "name": name,
            "job": job,
            "doctor_specialization": specializations,
        }
        doctors_data.append(doctor_info)

    return doctors_data


def extract_address_and_website(soup):
    """
    Извлекает адрес и ссылку на веб-сайт из HTML.

    Args:
        soup (BeautifulSoup): Объект парсинга HTML.

    Returns:
        tuple: Кортеж с адресом и веб-сайтом.
    """
    # Ищем пустой тег <a> с классом "address" и получаем следующий <a>
    address_tag = soup.find("a", class_="address")
    address = ""

    if address_tag:
        next_a_tag = address_tag.find_next_sibling("a")  # Находим следующий тег <a>
        if next_a_tag:
            address = next_a_tag.text.strip()

    # Ищем веб-сайт по стилю (цвет текста)
    website_tag = soup.find(
        "a", href=True, style=lambda value: value and "color" in value
    )
    website = website_tag.text.strip() if website_tag else ""

    return address, website


def find_url_by_clinic_name(clinic_name, input_csv_file):
    """
    Находит URL из списка, который заканчивается на последнее слово из clinic_name.

    Args:
        clinic_name (str): Название клиники.
        input_csv_file (str): Путь к CSV файлу со списком URL.

    Returns:
        str: Найденный URL или пустая строка, если URL не найден.
    """
    # Чтение списка URL из CSV
    urls = read_cities_from_csv(input_csv_file)

    # Получаем последнее слово из clinic_name
    last_word = clinic_name.split()[-1]

    # Проверяем каждый URL, заканчивается ли он на нужное слово
    for url in urls:
        if url.endswith(last_word):
            return url  # Возвращаем первый подходящий URL

    return ""  # Если URL не найден, возвращаем пустую строку


def parsing_html():
    """
    Обрабатывает HTML-файлы в указанной директории, извлекает данные из тегов, сохраняет в файл JSON.
    """
    output_file = Path("extracted_profile_data.json")
    extracted_data = {
        "project": "focus-gesundheit.de",
        "data": [],  # Список для хранения словарей
    }

    # Проверяем, существует ли директория
    if not html_directory.is_dir():
        logger.error(f"Директория {html_directory} не существует.")
        return

    for html_file in html_directory.glob("*.html"):
        try:
            with html_file.open(encoding="utf-8") as file:
                name = None
                image = None
                phone = None
                fax = None
                address = None
                clinic_name = None
                doctor_specialization = None
                incuranse = None
                email = None
                web = None
                languages = None
                transport_list = None
                doc_logo = None
                additional_info = None
                full_description = None
                url_doctor = None
                opening_hours = None
                polyclinics = []
                content = file.read()
                soup = BeautifulSoup(content, "lxml")
                script_json = soup.find("script", {"type": "application/ld+json"})
                # if script_json:
                clinic_overview = soup.find(
                    "div",
                    {"class": "overview"},
                )
                if clinic_overview:
                    clinics_raw = clinic_overview.find(
                        "div",
                        {"class": "card-header"},
                    )
                    if clinics_raw:
                        clinics = clinics_raw.find("h1")
                        if clinics:
                            clinic_name = clinics.text.strip()
                    doctor_specializations = clinic_overview.find("h2").find("span")
                    # Извлекаем текст из всех <li> элементов внутри <ul>
                    if doctor_specializations:
                        doctor_specialization = [doctor_specializations.text.strip()]
                    opening_hours = parse_opening_hours(clinic_overview)
                    # address_raw = clinic_overview.find("a", {"class": "address"})
                    # logger.info(address_raw.find("a"))
                    # if address_raw:
                    #     address = address_raw.text.strip()
                    # web_raw = soup.select_one(
                    #     "#main > div > div:nth-child(4) > div > section.informations > div.overview > div:nth-child(4) > a:nth-child(4)"
                    # )
                    # if web_raw:
                    #     web = web_raw.get("href")
                    address, web = extract_address_and_website(soup)
                doctor_specialization = extract_special_features(soup)
                services = extract_service_titles(soup)
                about_text = extract_about_text(soup)
                full_description = {
                    "title": "Über mich",
                    "Herzlich willkommen": about_text,
                }
                doctors_list = extract_doctors_data(soup)
                url_doctor = find_url_by_clinic_name(clinic_name, output_csv)

                # if script_json:
                #     doctor_json = json.loads(script_json.string.strip())

                #     # name = doctor_json.get("name", None)
                #     image = doctor_json.get("image", None)
                #     phone = doctor_json.get("telephone", None)
                #     if phone:
                #         phone = phone.replace(" ", "").replace("/", "")
                #         phone = format_phone_fax(phone)

                #     address_raw = doctor_json.get("address", {})
                #     if address_raw:
                #         streetAddress = address_raw.get("streetAddress", None)
                #         addressLocality = address_raw.get("addressLocality", None)
                #         postalCode = address_raw.get("postalCode", None)
                #         addressRegion = address_raw.get("addressRegion", None)
                #         addressCountry = address_raw.get("addressCountry", None)
                #         address = f"{streetAddress} {postalCode} {addressLocality}"
                # phone_number.append(phone)
                # firstname_raw = soup.find(
                #     "span",
                #     {"id": "firstname"},
                # )
                # lastname_raw = soup.find(
                #     "span",
                #     {"id": "lastname"},
                # )
                # if firstname_raw:
                #     firstname = firstname_raw.text.strip()
                # if lastname_raw:
                #     lastname = lastname_raw.text.strip()
                # name = f"{firstname} {lastname}"

                # fax_raw = soup.find(
                #     "span",
                #     {"id": "fax"},
                # )
                # if fax_raw:
                #     fax = fax_raw.text.strip().replace(" ", "").replace("/", "")
                #     fax = format_phone_fax(fax)
                # if fax is not None:
                #     phone_number.append(fax)

                # incuranse_raw = soup.select_one(
                #     "#detail_main > div.col-md-9.col-md-pull-3.detail-content > div > section.profile__content__overview > div:nth-child(5) > div > div.profile__content__content.col-sm-8 > div.editable--hidden-on-edit"
                # )
                # if incuranse_raw:
                #     incuranse_text = incuranse_raw.text.strip()  # "Kasse | Privat"
                #     # Обрабатываем и заменяем слова
                #     incuranse = [
                #         item.strip()
                #         .replace("Kasse", "Gesetzlich")
                #         .replace("Insurance", "Versicherung")
                #         for item in incuranse_text.split("|")
                #     ]
                # email_raw = soup.find("span", {"data-placeholder": "E-Mail"})
                # if email_raw:
                #     email = email_raw.text.strip()

                # languages_raw = soup.find(
                #     "ul", {"data-placeholder": "Sprachen auswählen"}
                # )
                # if languages_raw:
                #     languages = [
                #         li.get_text(strip=True) for li in languages_raw.find_all("li")
                #     ]

                # hours_list = soup.find(
                #     "ul", {"class": "profile__sidebar__open-hours-list"}
                # )

                # # Создаём словарь для хранения расписания
                # schedule = {}

                # if hours_list:
                #     # Проходим по всем элементам <li> в списке
                #     for item in hours_list.find_all("li"):
                #         # Извлекаем день недели
                #         day_tag = item.find(
                #             "div", {"class": "profile__sidebar__open-hours__day"}
                #         ).find("span")
                #         day = day_tag.text.strip() if day_tag else None

                #         # Извлекаем часы работы
                #         hours_div = item.find(
                #             "div", {"class": "profile__sidebar__open-hours__hour"}
                #         )
                #         if hours_div:
                #             # Извлекаем текст часов работы
                #             hours_text = hours_div.find(
                #                 "span", class_=False
                #             )  # Берём основной блок
                #             if hours_text:
                #                 hours = hours_text.get_text(strip=True)
                #             else:
                #                 hours = (
                #                     "geschlossen"  # Если элемента нет, значит закрыто
                #                 )

                #             # Добавляем в словарь
                #             if day:
                #                 schedule[day] = hours
                # # Преобразуем расписание
                # opening_hours = transform_schedule(schedule)
                # url_doctor_raw = soup.find("link", attrs={"rel": "canonical"})
                # if url_doctor_raw:
                #     url_doctor = url_doctor_raw.get("href")
                # transport_raw = soup.find("span", {"id": "infoTraffic"})
                # if transport_raw:
                #     # Извлекаем текст из атрибута или содержимого
                #     raw_data = transport_raw.text.strip()

                #     # Разделяем данные на строки
                #     transport_list = (
                #         raw_data.split("\n")
                #         if "\n" in raw_data
                #         else raw_data.split("  ")
                #     )

                #     # Убираем лишние пробелы
                #     transport_list = [
                #         line.strip() for line in transport_list if line.strip()
                #     ]
                # doc_logo_raw = soup.find("img", {"id": "doc-logo"})
                # if doc_logo_raw:
                #     doc_logo = doc_logo_raw.get("src")

                # additional_info_raw = soup.find(
                #     "ul", {"data-placeholder": "Patientenservices auswählen"}
                # )
                # if additional_info_raw:
                #     additional_info = [
                #         li.get_text(strip=True)
                #         for li in additional_info_raw.find_all("li")
                #     ]
                # description_raw = soup.find("span", {"data-editable-type": "ckeditor"})
                # if description_raw:
                #     # Найти все теги <p>
                #     paragraphs = description_raw.find_all("p")
                #     # Извлечь текст из каждого <p>
                #     description = [p.get_text(strip=True) for p in paragraphs]
                #     # Объединить текст, если требуется одна строка
                #     full_description = " ".join(description)
                # full_description = {
                #     "title": "Über mich",
                #     "Herzlich willkommen": full_description,
                # }
                polyclinic = {
                    # "phone_number": phone_number,
                    "website_doctor": web,
                    # "email": email,
                    "clinic_name": clinic_name,
                    "address": address,
                    "opening_hours": opening_hours,
                    "doctors_list": doctors_list,
                    # "transport_list": transport_list,
                }
                polyclinics.append(polyclinic)
                all_data = {
                    "name": name,
                    "url_doctor": url_doctor,
                    "doctor_specializations": doctor_specialization,
                    "description": full_description,
                    # "accepted_insurances": incuranse,
                    # "languages": languages,
                    "services": services,
                    "polyclinics": polyclinics,
                }
                # Добавляем данные в список
                extracted_data["data"].append(all_data)

        except Exception as e:
            logger.error(f"Ошибка при обработке файла {html_file.name}: {e}")
    # logger.info(extracted_data)
    try:
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Все данные сохранены в {output_file}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в файл {output_file}: {e}")


def parsin_xml():
    # Чтение файла sitemap.xml
    with open("sitemap_portal_practices.xml", "r", encoding="utf-8") as file:
        xml_content = file.read()

    # Разбор XML содержимого
    root = ET.fromstring(xml_content)

    # Пространство имен XML, используется для правильного извлечения данных
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    # Извлечение всех URL из тегов <loc>
    urls = [url.text.strip() for url in root.findall(".//ns:loc", namespace)]

    # Создание DataFrame с URL
    url_data = pd.DataFrame(urls, columns=["url"])

    # Запись URL в CSV файл
    url_data.to_csv("urls.csv", index=False)


if __name__ == "__main__":
    # parsin_xml()

    # main()
    parsing_html()
