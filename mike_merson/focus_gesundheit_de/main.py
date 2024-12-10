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
                address = None
                clinic_name = None

                content = file.read()
                soup = BeautifulSoup(content, "lxml")
                script_json = soup.find("script", {"type": "application/ld+json"})
                if script_json:
                    doctor_json = json.loads(script_json.string.strip())

                    name = doctor_json.get("name", None)
                    image = doctor_json.get("image", None)
                    phone = doctor_json.get("telephone", None)
                    address_raw = doctor_json.get("address", {})
                    if address_raw:
                        streetAddress = address_raw.get("streetAddress", None)
                        addressLocality = address_raw.get("addressLocality", None)
                        postalCode = address_raw.get("postalCode", None)
                        addressRegion = address_raw.get("addressRegion", None)
                        addressCountry = address_raw.get("addressCountry", None)
                        address = f"{streetAddress} {postalCode} {addressLocality} {addressCountry}"

                clinics_raw = soup.find(
                    "div",
                    {"class": "profile__sidebar-item profile__sidebar-item--highlight"},
                )
                if clinics_raw:
                    clinics = clinics_raw.find("p")
                    if clinics:
                        clinic_name = clinics.text.strip()

                logger.info(clinics)
                exit()
                # Извлекаем данные
                name = soup.find("h1", {"id": "profile-name-with-title"})
                if not title:
                    all_data = {"notPresent": True}
                    data_doctor = soup.find("div", {"id": "js-directory-doctor-page"})
                    if data_doctor:
                        # Извлекаем JSON из атрибута "data-props"
                        raw_json_data = data_doctor.get("data-props")

                        try:
                            # Парсим JSON из строки
                            parsed_data = json.loads(raw_json_data)

                            # Извлекаем необходимые данные
                            all_data["title"] = parsed_data.get("fullName")
                            all_data["speciality"] = parsed_data.get("speciality")

                            doctor_place = parsed_data.get("doctorPlace", {})
                            # all_data["address"] = doctor_place.get("address")
                            # all_data["zipcode"] = doctor_place.get("zipcode")
                            # all_data["city"] = doctor_place.get("city")
                            all_data["landline_number"] = doctor_place.get(
                                "landline_number"
                            )

                            all_data["address"] = (
                                f"{doctor_place.get('address')}, {doctor_place.get('zipcode')}{doctor_place.get('city')}"
                            )
                            extracted_data["data"].append(all_data)
                            continue
                        except json.JSONDecodeError as e:
                            logger.error(f"Ошибка декодирования JSON: {e}")
                            all_data["error"] = "Ошибка декодирования JSON"
                    else:
                        logger.warning(
                            f"Элемент с id 'js-directory-doctor-page' не найден {html_file}"
                        )
                        all_data["error"] = "Элемент не найден"
                speciality = soup.find("div", {"class": "dl-profile-header-speciality"})

                specialities = None
                if speciality:
                    # Извлекаем все элементы <span> внутри блока
                    spans = speciality.find_all("span")
                    # Объединяем текст из всех <span> в одну строку
                    raw_text = " ".join(span.text.strip() for span in spans)
                    # Разделяем строку по запятым и "und"
                    specialities = [
                        spec.strip()
                        for spec in raw_text.replace(" und ", ", ").split(",")
                    ]
                else:
                    specialities = None

                dl_profile = soup.find("div", {"class": "dl-profile-text"})
                insurance_types = None
                if dl_profile:
                    raw_text = dl_profile.text.strip()
                    # Разделяем строку по ключевым словам "und", "sowie"
                    insurance_types = [
                        item.strip()
                        for item in raw_text.replace(" sowie ", ", ")
                        .replace(" und ", ", ")
                        .split(",")
                    ]
                dl_profile_skills = soup.find("div", {"class": "dl-profile-skills"})

                # Обрабатываем навыки
                skills = []
                if dl_profile_skills:
                    profile_skill_raw = dl_profile_skills.find_all(
                        "div", {"class": "dl-profile-skill-chip"}
                    )
                    for skill_raw in profile_skill_raw:
                        if skill_raw:
                            skills.append(skill_raw.text.strip())
                image_profile = ld_json.get("image", None)
                image_profile = f"https:{image_profile}"

                dl_profile_practice_transport = soup.select_one(
                    "#main-content > div.dl-profile-bg.dl-profile > div.dl-profile-wrapper.dl-profile-responsive-wrapper.dl-profile-wrapper-gap > div.dl-profile-body-wrapper.mt-8 > div:nth-child(8) > div > div.dl-profile-card-content > div:nth-child(3)"
                )
                # Извлекаем текст всех элементов <span>
                dl_transport = []
                if dl_profile_practice_transport:
                    spans = dl_profile_practice_transport.find_all("span")
                    dl_transport = [span.text.strip() for span in spans]

                practice_map_div = soup.find("div", {"class": "js-maps-doctor-map"})
                if practice_map_div:
                    data_props = practice_map_div.get("data-props")

                    if data_props:
                        # Парсим data-props как JSON
                        practice_data = json.loads(data_props)
                        address = practice_data.get("fullAddress")
                        latitude = practice_data.get("lat")
                        longitude = practice_data.get("lng")
                dl_profile_title_raw = soup.find(
                    "h2",
                    {
                        "class": "dl-profile-card-title dl-text dl-text-title dl-text-bold dl-text-s dl-text-neutral-150"
                    },
                )
                dl_profile_title = (
                    dl_profile_title_raw.text.strip() if dl_profile_title_raw else None
                )

                # Извлекаем описание
                dl_profile_bio_raw = soup.find(
                    "p", {"class": "dl-profile-text js-bio dl-profile-bio"}
                )
                dl_profile_bio = (
                    dl_profile_bio_raw.text.strip() if dl_profile_bio_raw else None
                )

                # Формируем результат
                if dl_profile_title and dl_profile_bio:
                    description = {
                        "title": "Profil",
                        "Herzlich willkommen": dl_profile_bio,
                    }
                    # logger.info(description)
                else:
                    description = None
                    # logger.error(html_file)
                    # logger.warning("Данные профиля отсутствуют.")

                language_section = soup.select_one(
                    ".dl-profile-row-section h3.dl-profile-card-subtitle"
                )

                languages = []
                if language_section and "Gesprochene Sprachen" in language_section.text:
                    # Ищем текст внутри родительского <div>
                    parent_div = language_section.find_parent()
                    if parent_div:
                        # Извлекаем текст, удаляем заголовок и разделяем по "und" и пробелам
                        raw_languages = parent_div.text.replace(
                            "Gesprochene Sprachen", ""
                        ).strip()
                        languages = [
                            lang.strip() for lang in raw_languages.split(" und ")
                        ]
                else:
                    languages = None
                    # logger.warning("Раздел 'Gesprochene Sprachen' не найден.")
                dl_profile_history_raw = soup.find_all(
                    "div", {"class": "dl-profile-card-section dl-profile-history"}
                )
                history_data = []
                for history in dl_profile_history_raw:
                    section_title = (
                        history.find("h3").get_text(strip=True)
                        if history.find("h3")
                        else "Без заголовка"
                    )
                    section_text = history.get_text(strip=True, separator="\n")
                    history_data.append(
                        {"title": section_title, "content": section_text}
                    )
                openingHours = ld_json.get("openingHours", [])
                phone_number = ld_json.get("telephone", None)
                clinic_name_raw = soup.find(
                    "div", {"class": "dl-profile-practice-name"}
                )
                if clinic_name_raw:
                    clinic_name = clinic_name_raw.text.strip()
                # Ищем элемент с заголовком "Website"
                website_section = soup.find("h3", string="Website")

                # Проверяем, нашли ли элемент
                if website_section:
                    # Переходим к родительскому блоку и ищем ссылку
                    link = website_section.find_next("a", href=True)
                    if link:
                        href = link["href"]

                # Сохраняем данные
                all_data = {
                    "title": title.text.strip() if title else None,
                    "services": skills,
                    "image_profile": image_profile,
                    "website_section": href,
                    "dl_language": languages,
                }
                all_data["specialities"] = specialities
                all_data["insurance"] = insurance_types
                all_data["transport"] = dl_transport
                all_data["description"] = description
                all_data["history_data"] = history_data
                polyclinic_data = {
                    "polyclinics": [
                        {
                            "phone_number": [phone_number],
                            "clinic_name": clinic_name,
                            "address": address,
                            "opening_hours": openingHours,
                            "gps": [{"lat": latitude, "lng": longitude}],
                            "offered_services": None,
                        }
                    ]
                }
                # Добавляем данные polyclinics в all_data
                all_data.update(polyclinic_data)

                # Добавляем all_data в список
                extracted_data["data"].append(all_data)
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {html_file.name}: {e}")
    # logger.info(extracted_data)
    # Сохраняем данные в файл JSON
    try:
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        # logger.info(f"Все данные сохранены в {output_file}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в файл {output_file}: {e}")


if __name__ == "__main__":
    # main()
    parsing_html()
