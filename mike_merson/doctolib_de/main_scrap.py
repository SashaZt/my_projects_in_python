# ПАРСИНГ АСИНХРОННЫЙ
import asyncio
import json
import logging
import re
from pathlib import Path

import aiofiles
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

current_directory = Path.cwd()

html_directory = current_directory / "html"
html_directory.mkdir(exist_ok=True, parents=True)

output_file = Path("extracted_profile_data.json")
CONCURRENT_TASKS = 50  # Количество одновременных задач


async def process_html_file(html_file, extracted_data):
    """
    Асинхронно обрабатывает один HTML-файл и добавляет данные в общий список.
    """
    try:
        async with aiofiles.open(html_file, mode="r", encoding="utf-8") as file:
            content = await file.read()
            description = None
            clinic_name = None
            address = None
            latitude = None
            longitude = None
            languages = None
            dl_transport = None
            dl_profile_bio = None
            href = None
            soup = BeautifulSoup(content, "lxml")
            script_tags = soup.find("script", {"type": "application/ld+json"})
            ld_json = json.loads(script_tags.string.strip())
            # Извлекаем данные
            name = soup.find("span", {"itemprop": "name"})
            if not name:
                all_data = {"notPresent": True}
                data_doctor = soup.find("div", {"id": "js-directory-doctor-page"})
                if data_doctor:
                    script_tags_doctor = soup.find(
                        "script", {"type": "application/ld+json"}
                    )
                    script_json = json.loads(script_tags_doctor.string.strip())
                    # Извлекаем JSON из атрибута "data-props"
                    # raw_json_data = data_doctor.get("data-props")

                    try:
                        # Парсим JSON из строки
                        # parsed_data = json.loads(raw_json_data)
                        speciality = script_json.get("medicalSpecialty")
                        speciality_array = [
                            item.strip()
                            for item in re.split(r"/|-|und", speciality)
                            if item.strip()
                        ]

                        # Извлекаем необходимые данные
                        all_data["phone_number"] = script_json.get("telephone")
                        all_data["name"] = script_json.get("name")
                        all_data["speciality"] = speciality_array

                        doctor_place = script_json.get("address", {})
                        streetAddress = doctor_place.get("streetAddress", None)
                        postalCode = doctor_place.get("postalCode", None)
                        addressLocality = doctor_place.get("addressLocality", None)

                        all_data["address"] = (
                            f"{streetAddress}, {postalCode}, {addressLocality}"
                        )
                        # extracted_data["data"].append(all_data)
                        return all_data
                    except json.JSONDecodeError as e:
                        logger.error(f"Ошибка декодирования JSON: {e}")
                        all_data["error"] = "Ошибка декодирования JSON"
                else:
                    # logger.warning(
                    #     f"Элемент с id 'js-directory-doctor-page' не найден {html_file}"
                    # )
                    return None
            speciality = soup.find("div", {"class": "dl-profile-header-speciality"})

            specialities = None
            if speciality:
                # Извлекаем все элементы <span> внутри блока
                spans = speciality.find_all("span")
                # Объединяем текст из всех <span> в одну строку
                raw_text = " ".join(span.text.strip() for span in spans)
                # Разделяем строку по запятым и "und"
                specialities = [
                    spec.strip() for spec in raw_text.replace(" und ", ", ").split(",")
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

            # Проверяем, существует ли значение image
            if image_profile:
                image_profile = f"https:{image_profile}"
                # Проверяем, не является ли ссылка аватаром по умолчанию
                if (
                    image_profile
                    == "https://assets.doctolib.fr/images/default_doctor_avatar.png"
                ):
                    # logger.info(html_file)
                    return None

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
                        lang.strip()
                        for lang in re.split(r" und |, ", raw_languages)
                        if lang.strip()
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
                history_data.append({"title": section_title, "content": section_text})
            openingHours = ld_json.get("openingHours", [])
            phone_number = ld_json.get("telephone", None)
            clinic_name_raw = soup.find("div", {"class": "dl-profile-practice-name"})
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
                "name": name.text.strip() if name else None,
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
        # Добавляем извлечённые данные в список
        extracted_data.append(all_data)
    except Exception as e:
        return None


async def save_data_to_json(data, file_path):
    """
    Асинхронно сохраняет данные в JSON-файл.
    """
    try:
        async with aiofiles.open(file_path, mode="w", encoding="utf-8") as file:
            await file.write(json.dumps(data, ensure_ascii=False, indent=4))
        logger.info(f"Все данные сохранены в {file_path}")
    except Exception as e:
        logger.error(f"Ошибка сохранения данных в файл {file_path}: {e}")


async def parsing_html_async():
    """
    Асинхронно обрабатывает HTML-файлы в указанной директории.
    """
    extracted_data = {
        "project": "doctolib.de",
        "data": [],
    }

    if not html_directory.is_dir():
        logger.error(f"Директория {html_directory} не существует.")
        return

    html_files = list(html_directory.glob("*.html"))
    logger.info(f"Найдено {len(html_files)} файлов для обработки.")

    sem = asyncio.Semaphore(CONCURRENT_TASKS)  # Ограничение на одновременные задачи

    async def sem_task(file_path):
        async with sem:
            result = await process_html_file(file_path, extracted_data["data"])
            if result:  # Если результат не None, добавляем в список
                extracted_data["data"].append(result)

    tasks = [sem_task(file) for file in html_files]
    await asyncio.gather(*tasks)

    logger.info(f"Обработано {len(extracted_data['data'])} файлов.")
    # Сохраняем результат
    await save_data_to_json(extracted_data, output_file)


# Запуск
if __name__ == "__main__":
    asyncio.run(parsing_html_async())
