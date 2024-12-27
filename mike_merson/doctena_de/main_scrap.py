import json
import threading
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

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


def format_phone_fax(number):
    if number and not number.startswith("+49"):
        return f"+49{number}"
    return number


def transform_schedule(schedule):
    """
    Преобразует расписание в формат с диапазонами времени для каждого дня недели.
    """
    # Сопоставление дней недели с числами
    days_mapping = {
        "MO": 0,
        "DI": 1,
        "MI": 2,
        "DO": 3,
        "FR": 4,
        "SA": 5,
        "SO": 6,
    }

    # Предопределенные диапазоны времени для заполнения
    predefined_ranges = {
        0: [["08:30", "13:00"], ["14:00", "18:00"]],  # Понедельник
        1: [["08:30", "13:00"], ["14:00", "19:00"]],  # Вторник
        2: [["08:30", "14:00"]],  # Среда
        3: [["08:30", "13:00"], ["14:00", "18:00"]],  # Четверг
        4: [["08:30", "14:00"]],  # Пятница
        5: [],  # Суббота
        6: [],  # Воскресенье
    }

    # Формируем расписание в новом формате
    transformed_schedule = []

    for day_code, time in schedule.items():
        day = days_mapping[day_code]  # Преобразуем код дня в число
        if time.lower() == "geschlossen":
            # Если "geschlossen", то не добавляем диапазоны
            transformed_schedule.append({"day": day, "ranges": []})
        else:
            # Добавляем предопределенные диапазоны для рабочего дня
            transformed_schedule.append({"day": day, "ranges": predefined_ranges[day]})

    return transformed_schedule


def process_file(html_file: Path, lock: threading.Lock, data_list: list):
    try:
        with html_file.open(encoding="utf-8") as file:
            content = file.read()
            soup = BeautifulSoup(content, "lxml")
            name = firstname = lastname = image = phone = fax = address = (
                clinic_name
            ) = None
            doctor_specialization = incuranse = email = web = languages = (
                transport_list
            ) = None
            doc_logo = additional_info = full_description = url_doctor = None
            polyclinics = []
            phone_number = []
            script_json = soup.find("script", {"type": "application/ld+json"})
            if script_json:
                doctor_json = json.loads(script_json.string.strip())

                # name = doctor_json.get("name", None)
                # image = doctor_json.get("image", None)
                phone = doctor_json.get("telephone", None)
                if phone:
                    phone = phone.replace(" ", "").replace("/", "")
                    phone = format_phone_fax(phone)

                address_raw = doctor_json.get("address", {})
                if address_raw:
                    streetAddress = address_raw.get("streetAddress", None)
                    addressLocality = address_raw.get("addressLocality", None)
                    postalCode = address_raw.get("postalCode", None)
                    addressRegion = address_raw.get("addressRegion", None)
                    addressCountry = address_raw.get("addressCountry", None)
                    address = f"{streetAddress} {postalCode} {addressLocality}"
            phone_number.append(phone)

            image_tag = soup.find(
                "div",
                {"id": "js-profile-picture"},
            )
            logger.info(image_tag)
            if image_tag:
                image = image_tag.find("img").get("src")
            name_tag = soup.find(
                "h1",
                {"class": "title-seo dsg-title-1 dsg-no-mg-bottom dsg-no-mg-top"},
            )
            if name_tag:
                name = name_tag.text.strip().replace("Dr. ", "")

            clinics_raw = soup.find(
                "div",
                {"class": "profile__sidebar-item profile__sidebar-item--highlight"},
            )
            if clinics_raw:
                clinics = clinics_raw.find("p")
                if clinics:
                    clinic_name = clinics.text.strip()
            fax_raw = soup.find(
                "span",
                {"id": "fax"},
            )
            if fax_raw:
                fax = fax_raw.text.strip().replace(" ", "").replace("/", "")
                fax = format_phone_fax(fax)
            if fax is not None:
                phone_number.append(fax)
            doctor_specializations = soup.select_one(
                "#detail_main > div.col-md-9.col-md-pull-3.detail-content > div > section.profile__content__overview > div:nth-child(2) > div > div.profile__content__content.profile__content__content--highlight.col-sm-8 > ul"
            )
            # Извлекаем текст из всех <li> элементов внутри <ul>
            if doctor_specializations:
                doctor_specialization = [
                    li.get_text(strip=True)
                    for li in doctor_specializations.find_all("li")
                ]
            incuranse_raw = soup.select_one(
                "#detail_main > div.col-md-9.col-md-pull-3.detail-content > div > section.profile__content__overview > div:nth-child(5) > div > div.profile__content__content.col-sm-8 > div.editable--hidden-on-edit"
            )
            if incuranse_raw:
                incuranse_text = incuranse_raw.text.strip()  # "Kasse | Privat"
                # Обрабатываем и заменяем слова
                incuranse = [
                    item.strip()
                    .replace("Kasse", "Gesetzlich")
                    .replace("Insurance", "Versicherung")
                    for item in incuranse_text.split("|")
                ]
            email_raw = soup.find("span", {"data-placeholder": "E-Mail"})
            if email_raw:
                email = email_raw.text.strip()
            web_raw = soup.find("span", {"id": "homepage1"})
            if web_raw:
                web = web_raw.text.strip()

            languages_raw = soup.find("ul", {"data-placeholder": "Sprachen auswählen"})
            if languages_raw:
                languages = [
                    li.get_text(strip=True) for li in languages_raw.find_all("li")
                ]

            hours_list = soup.find("ul", {"class": "profile__sidebar__open-hours-list"})

            # Создаём словарь для хранения расписания
            schedule = {}

            if hours_list:
                # Проходим по всем элементам <li> в списке
                for item in hours_list.find_all("li"):
                    # Извлекаем день недели
                    day_tag = item.find(
                        "div", {"class": "profile__sidebar__open-hours__day"}
                    ).find("span")
                    day = day_tag.text.strip() if day_tag else None

                    # Извлекаем часы работы
                    hours_div = item.find(
                        "div", {"class": "profile__sidebar__open-hours__hour"}
                    )
                    if hours_div:
                        # Извлекаем текст часов работы
                        hours_text = hours_div.find(
                            "span", class_=False
                        )  # Берём основной блок
                        if hours_text:
                            hours = hours_text.get_text(strip=True)
                        else:
                            hours = "geschlossen"  # Если элемента нет, значит закрыто

                        # Добавляем в словарь
                        if day:
                            schedule[day] = hours
            # Преобразуем расписание
            opening_hours = transform_schedule(schedule)
            url_doctor_raw = soup.find("link", attrs={"rel": "canonical"})
            if url_doctor_raw:
                url_doctor = url_doctor_raw.get("href")
            transport_raw = soup.find("span", {"id": "infoTraffic"})
            if transport_raw:
                # Извлекаем текст из атрибута или содержимого
                raw_data = transport_raw.text.strip()

                # Разделяем данные на строки
                transport_list = (
                    raw_data.split("\n") if "\n" in raw_data else raw_data.split("  ")
                )

                # Убираем лишние пробелы
                transport_list = [
                    line.strip() for line in transport_list if line.strip()
                ]
            doc_logo_raw = soup.find("img", {"id": "doc-logo"})
            if doc_logo_raw:
                doc_logo = doc_logo_raw.get("src")

            additional_info_raw = soup.find(
                "ul", {"data-placeholder": "Patientenservices auswählen"}
            )
            if additional_info_raw:
                additional_info = [
                    li.get_text(strip=True) for li in additional_info_raw.find_all("li")
                ]
            description_raw = soup.find("span", {"data-editable-type": "ckeditor"})
            if description_raw:
                # Найти все теги <p>
                paragraphs = description_raw.find_all("p")
                # Извлечь текст из каждого <p>
                description = [p.get_text(strip=True) for p in paragraphs]
                # Объединить текст, если требуется одна строка
                full_description = " ".join(description)
            full_description = {
                "title": "Über mich",
                "Herzlich willkommen": full_description,
            }
            polyclinic = {
                "phone_number": phone_number,
                "website_doctor": web,
                "email": email,
                "clinic_name": clinic_name,
                "address": address,
                "opening_hours": opening_hours,
                "doc_logo": doc_logo,
                "transport_list": transport_list,
            }
            polyclinics.append(polyclinic)
            all_data = {
                "name": name,
                "img": image,
                "url_doctor": url_doctor,
                "doctor_specializations": doctor_specialization,
                "description": full_description,
                "accepted_insurances": incuranse,
                "languages": languages,
                "services": additional_info,
                "polyclinics": polyclinics,
            }

            with lock:
                data_list.append(all_data)
    except Exception as e:
        logger.error(f"Ошибка при обработке файла {html_file.name}: {e}")


def parsing_html(thread_count: int = 4):
    output_file = Path("extracted_profile_data.json")
    extracted_data = {"project": "focus-gesundheit.de", "data": []}
    lock = threading.Lock()

    html_files = list(html_directory.glob("*.html"))

    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        for html_file in html_files:
            executor.submit(process_file, html_file, lock, extracted_data["data"])

    try:
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Все данные сохранены в {output_file}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в файл {output_file}: {e}")


if __name__ == "__main__":
    parsing_html(thread_count=50)
