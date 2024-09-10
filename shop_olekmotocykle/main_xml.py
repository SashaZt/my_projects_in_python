import requests
import xml.etree.ElementTree as ET
import pandas as pd
import time
import os
from configuration.logger_setup import logger

current_directory = os.getcwd()

"""Скачать XML файл"""


def get_xml():
    logger.info("Качаем файл XML")
    url = "https://pim.olekmotocykle.com/xml?id=85&hash=be0525b9258c18c3452ee7bd80bcf32e591b48a4ca3574f2fd0d80b8a3f450b6"
    response = requests.get(url)
    filename_xml = os.path.join(current_directory, "output.xml")
    if response.status_code == 200:
        with open(filename_xml, "wb") as file:
            file.write(response.content)
        print("XML файл успешно сохранен")
    else:
        print("Ошибка при загрузке XML:", response.status_code)


"""Парсим файл XML"""


# Function to parse product element
def parse_product(product):
    data = {
        "id": product.attrib["id"],
        "symbol": product.find("symbol").text,
        "kod": product.find("kod").text,
        # "ean": product.find("ean").text if product.find("ean").text else "",
        "name": product.find("name").text,
        "marka": product.find("marka").text,
        # "imgs": [i.attrib["url"] for i in product.find("imgs").findall("i")],
        "category": product.find("category").text.strip(),
        "price": float(product.find("price").text),
        "quantity": int(product.find("quantity").text),
    }
    return data


def parsing_xml():
    # Загрузка XML из файла
    filename_xml = os.path.join(current_directory, "output.xml")
    tree = ET.parse(filename_xml)
    root = tree.getroot()
    # Extract data from XML
    products = []
    for product in root.findall("product"):
        products.append(parse_product(product))
    # Преобразование данных в DataFrame
    df = pd.DataFrame(products)

    # Запись данных в .xlsx файл
    filename_xlsx = os.path.join(current_directory, "output.xlsx")
    df.to_excel(filename_xlsx, index=False)
    logger.info(f"Файл сохранен {filename_xlsx}")


def delete():
    filename_xml = os.path.join(current_directory, "output.xml")
    filename_xlsx = os.path.join(current_directory, "output.xlsx")
    if os.path.exists(filename_xlsx):
        os.remove(filename_xml)
    time.sleep(5)


if __name__ == "__main__":
    get_xml()
    # parsing_xml()
    # delete()
