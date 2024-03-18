import requests
import xml.etree.ElementTree as ET
import pandas as pd


"""Скачать XML файл"""
def get_xml():
    url = "https://www.larsson.pl/webapi/stocks/088087.xml"
    response = requests.get(url)

    if response.status_code == 200:
        with open('output.xml', 'wb') as file:
            file.write(response.content)
        print("XML файл успешно сохранен как 'output.xml'")
    else:
        print("Ошибка при загрузке XML:", response.status_code)


"""Парсим файл XML"""
def parsing_xml():
    # Загрузка XML из файла
    tree = ET.parse('output.xml')
    root = tree.getroot()

    # Создание списка для хранения данных из элементов
    items_data = []

    # Итерация по элементам <ITEM>
    for item in root.findall('.//ITEM'):
        item_info = {
            "NUMBER": item.find('NUMBER').text,
            "NAME": item.find('NAME').text,
            "RETAIL_NET_PRICE": item.find('RETAIL_NET_PRICE').text,
            "STOCK": item.find('STOCK').text,
            "SUPPLIER_ON_STOCK": item.find('SUPPLIER_ON_STOCK').text
        }

        items_data.append(item_info)

    # Преобразование данных в DataFrame
    df = pd.DataFrame(items_data)

    # Запись данных в .xlsx файл
    df.to_excel("output.xlsx", index=False)


if __name__ == '__main__':
    get_xml()
    parsing_xml()