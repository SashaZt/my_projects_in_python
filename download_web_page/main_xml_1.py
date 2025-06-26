import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

from config import Config, logger, paths


def extract_contact_info(html_file):
    """
    Извлекает контактную информацию из HTML-файла и возвращает словарь.
    """
    try:
        # Читаем HTML-файл
        with open(html_file, "r", encoding="utf-8") as file:
            content = file.read()
        soup = BeautifulSoup(content, "html.parser")

        # Инициализируем словарь для контактов
        contact_info = {
            "address": "",
            "phones": "",
            "website": "",
            "email": "",
            "company_name": "",
            "inn": "",
            "license": "",
            "instagram": "",
            "whatsapp": "",
        }

        # Находим div с классом builder-view-details
        details_div = soup.find("div", class_="builder-view-details")
        if details_div:
            # Получаем все div элементы внутри details_div
            all_divs = details_div.find_all("div", recursive=False)

            for div in all_divs:
                div_text = div.get_text(strip=True)

                # Извлекаем адрес
                if div_text.startswith("Адрес:"):
                    contact_info["address"] = div_text.replace("Адрес:", "").strip()

                # Извлекаем телефоны
                elif div_text.startswith("Телефоны:"):
                    phones = []
                    phone_links = div.find_all("a", href=lambda x: x and "tel:" in x)
                    for link in phone_links:
                        phone = link.get_text(strip=True)
                        if phone:  # Пропускаем пустые телефоны
                            phones.append(phone)
                    if phones:
                        contact_info["phones"] = ", ".join(phones)

                # Извлекаем email (строка содержит @ но не начинается с "ОсОО")
                elif "@" in div_text and not div_text.startswith("ОсОО"):
                    contact_info["email"] = div_text.strip()

                # Извлекаем данные компании (строка начинается с "ОсОО")
                elif div_text.startswith("ОсОО"):
                    # Регулярное выражение для извлечения названия компании и ИНН
                    match = re.search(r'ОсОО\s*"([^"]+)"\s*,\s*ИНН\s*(\d+)', div_text)
                    if match:
                        contact_info["company_name"] = f'ОсОО "{match.group(1)}"'
                        contact_info["inn"] = match.group(2)
                    else:
                        # Если регулярка не сработала, берем всю строку как название компании
                        contact_info["company_name"] = div_text

                # Извлекаем лицензию
                elif div_text.startswith("Лицензия:"):
                    contact_info["license"] = div_text.replace("Лицензия:", "").strip()

                # Проверяем на наличие социальных ссылок в этом div
                elif div.find("div", class_="builder-social-links"):
                    social_div = div.find("div", class_="builder-social-links")
                    if social_div:
                        for link in social_div.find_all("a", href=True):
                            href = link.get("href")
                            if "instagram" in href.lower():
                                contact_info["instagram"] = href
                            elif "wa.me" in href.lower():
                                contact_info["whatsapp"] = href

            # Также проверяем прямые ссылки на веб-сайт
            website_link = details_div.find("a", class_="builder-site-url")
            if website_link:
                contact_info["website"] = website_link.get_text(strip=True)

            # Дополнительная проверка для социальных ссылок на верхнем уровне
            social_div = details_div.find("div", class_="builder-social-links")
            if social_div:
                for link in social_div.find_all("a", href=True):
                    href = link.get("href")
                    if "instagram" in href.lower():
                        contact_info["instagram"] = href
                    elif "wa.me" in href.lower():
                        contact_info["whatsapp"] = href

        return contact_info

    except FileNotFoundError:
        logger.error(f"Файл не найден: {html_file}")
        return {}
    except Exception as e:
        logger.error(f"Ошибка при обработке {html_file}: {str(e)}")
        return {}


def main():
    """
    Обрабатывает все HTML-файлы в директории, собирает контакты и сохраняет в Excel.
    """
    all_contacts = []
    html_files = list(paths.html.glob("*.html"))

    if not html_files:
        logger.warning("HTML-файлы не найдены в директории")
        print("HTML-файлы не найдены")
        return

    for html_file in html_files:
        contact_info = extract_contact_info(html_file)
        if contact_info:
            all_contacts.append(contact_info)
            logger.info(f"Извлечены контакты из {html_file}")
            # Выводим извлеченные данные для отладки
            print(f"\nИзвлечено из {html_file}:")
            for key, value in contact_info.items():
                if value:  # Показываем только заполненные поля
                    print(f"  {key}: {value}")

    if all_contacts:
        # Создаем DataFrame из списка словарей
        df = pd.DataFrame(all_contacts)

        # Задаем порядок и названия столбцов
        columns_order = [
            "company_name",
            "inn",
            "address",
            "phones",
            "website",
            "email",
            "license",
            "instagram",
            "whatsapp",
        ]
        column_names = [
            "Название компании",
            "ИНН",
            "Адрес",
            "Телефоны",
            "Веб-сайт",
            "Email",
            "Лицензия",
            "Instagram",
            "WhatsApp",
        ]

        # Фильтруем только существующие столбцы и переименовываем
        existing_columns = [col for col in columns_order if col in df.columns]
        df = df[existing_columns]
        df.columns = [
            column_names[columns_order.index(col)] for col in existing_columns
        ]

        # Сохраняем в Excel
        output_file = "contacts.xlsx"
        df.to_excel(output_file, index=False, engine="openpyxl")
        logger.info(f"Контакты сохранены в {output_file}")
        print(f"\nКонтакты сохранены в {output_file}")

        # Выводим данные в консоль для проверки
        print("\nИтоговая таблица:")
        print(df.to_string(index=False))
    else:
        logger.warning("Контактная информация не найдена")
        print("Контактная информация не найдена")


if __name__ == "__main__":
    main()
