# -*- mode: python ; coding: utf-8 -*-
# Собираем данные из html файлов в products.csv
from bs4 import BeautifulSoup
import csv
import glob
import os


def parsing_products():
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    products_path = os.path.join(temp_path, "products")

    folder = os.path.join(products_path, "*.html")
    files_html = glob.glob(folder)
    heandler = [
        "company_name",
        "business_type",
        "company_location",
        "web_site",
        "main_phone",
        "local_phone",
        "owner_manager",
        "contact",
    ]
    with open("products.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(heandler)  # Записываем заголовки только один раз
        for item in files_html[:20]:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, "lxml")
            try:
                company_information = soup.find_all(
                    "div", attrs={"class": "panel-body"}
                )[0]
            except:
                continue
            contact_information = soup.find_all("div", attrs={"class": "panel-body"})[1]

            company_name = (
                soup.find("h1", attrs={"style": "display:inline"}).get_text().strip()
            )
            company_location = (
                company_information.find("address").text.replace("\n", " ").strip()
            )
            try:
                web_site = soup.find("a", attrs={"id": "webSite"})
                if web_site is not None:
                    web_site = web_site.get_text().strip()
            except:
                web_site = None
            main_phone = (
                contact_information.find("a", attrs={"id": "listingPhone"})
                .get_text()
                .strip()
            )
            local_phone = (
                contact_information.find("a", attrs={"id": "localPhone"})
                .get_text()
                .strip()
            )
            owner_manager = (
                company_information.find("span", attrs={"id": "principalContact"})
                .get_text()
                .strip()
            )
            contact = (
                contact_information.find("span", attrs={"id": "contactNames"})
                .get_text()
                .strip()
            )
            paragraphs = company_information.find_all("p")
            business_type = ""
            # Проходим по каждому параграфу
            for paragraph in paragraphs:
                # Если в параграфе есть текст 'Business Type:'
                if "Business Type:" in paragraph.text:
                    # Извлекаем текст после 'Business Type:'
                    business_type = paragraph.text.split("Business Type:")[1].strip()
                    # prin//t(business_type)  # Выведет: Carrier
            # business_type = company_information.find('h1', attrs={'style': 'display:inline'}).text.strip()
            datas = [
                company_name,
                business_type,
                company_location,
                web_site,
                main_phone,
                local_phone,
                owner_manager,
                contact,
            ]
            writer.writerow(datas)


if __name__ == "__main__":
    parsing_products()
