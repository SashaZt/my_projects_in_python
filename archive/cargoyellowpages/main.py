import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

# Путь к папкам
current_directory = Path.cwd()
html_directory = current_directory / "html"

html_directory.mkdir(exist_ok=True, parents=True)
# Набор для уникальных записей
# Извлечение данных компаний
companies = []

for html_file in html_directory.glob("*.html"):
    # Загрузка HTML-файла
    with open(html_file, "r", encoding="utf-8") as file:
        html_content = file.read()

    # Парсинг HTML с помощью BeautifulSoup
    soup = BeautifulSoup(html_content, "lxml")

    # Поиск таблицы с данными
    table = soup.find("table", id="AutoNumber7")
    if not table:
        print("Таблица данных не найдена в HTML.")
        exit()

    # Функция очистки телефона и факса

    def clean_phone_fax(number):
        return (
            re.sub(r"[^\d+]", "", number) if number else "N/A"
        )  # Убираем лишние символы

    # Извлечение данных компаний
    for entry in table.find_all("span", style="text-transform: uppercase"):
        # Извлечение и объединение названия компании
        name_parts = entry.get_text(separator=" ", strip=True)
        next_sibling = entry.find_next("b")
        if next_sibling and next_sibling.find("br"):
            name_parts += " " + next_sibling.get_text(separator=" ", strip=True)

        # # Телефон
        # phone = entry.find_next("img", alt="Phone No.")
        # phone = (
        #     clean_phone_fax(phone.next_sibling.strip())
        #     if phone and phone.next_sibling
        #     else "N/A"
        # )
        # Извлечение телефона
        phone_tag = entry.find_next("img", alt="Phone No.")  # Находим тег для телефона
        phone = (
            clean_phone_fax(phone_tag.next_sibling.strip())
            if phone_tag and phone_tag.next_sibling
            else "N/A"
        )
        fax_tag = entry.find_next("img", alt="Fax No.")  # Находим тег для факса
        fax = (
            clean_phone_fax(fax_tag.next_sibling.strip())
            if fax_tag and fax_tag.next_sibling
            else "N/A"
        )

        # # Факс
        # fax = entry.find_next("img", alt="Fax No.")
        # fax = clean_phone_fax(fax.next_sibling.strip()) if fax else "N/A"

        # Email
        # email_img = entry.find_next("img", alt="Email")
        # if email_img:
        #     email_parts = email_img.next_sibling.strip().split("<img")
        #     email_prefix = email_parts[0].replace(" ", "")
        #     email_suffix = (
        #         email_img.find_next("img", alt="@").next_sibling.strip()
        #         if email_img.find_next("img", alt="@")
        #         else ""
        #     )
        #     email = f"{email_prefix}@{email_suffix}".strip()
        #     email = email.replace(":", "")
        # else:
        #     email = "N/A"

        # URL
        # url = entry.find_next("img", alt="URL")
        # url = url.next_sibling.strip() if url else "N/A"
        # url = url.replace(":", "").replace("&nbsp;", "").strip()

        # Сохранение данных компании
        companies.append(
            {
                "Company": name_parts.strip(),
                "Phone": phone,
                "Fax": fax,
                # "Email": email,
                # "URL": url,
            }
        )


# Сохранение данных в Excel
df = pd.DataFrame(companies)
output_file = "NETHERLANDS.xlsx"
df.to_excel(output_file, index=False)
print(f"Данные успешно сохранены в файл {output_file}.")
