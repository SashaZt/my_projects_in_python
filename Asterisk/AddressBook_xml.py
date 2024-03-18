import pandas as pd
import numpy as np
from lxml import etree as ET

# Читаем CSV-файл
df = pd.read_csv('AddressBook.csv', sep=';')

# Создаем корневой элемент XML
root = ET.Element('AddressBook')

# Перебираем все строки DataFrame
for i in df.index:
    # Создаем элемент Contact
    contact = ET.SubElement(root, 'Contact')

    # Добавляем элементы FirstName и LastName
    first_name = df.loc[i, 'FirstName']
    last_name = df.loc[i, 'LastName']
    ET.SubElement(contact, 'FirstName').text = "" if pd.isnull(first_name) else str(first_name)
    ET.SubElement(contact, 'LastName').text = "" if pd.isnull(last_name) else str(last_name)

    # Создаем элемент Phone и его подэлементы
    phone_number = df.loc[i, 'Phone']
    phone = ET.SubElement(contact, 'Phone')
    ET.SubElement(phone, 'phonenumber').text = "" if pd.isnull(phone_number) else str(phone_number)
    ET.SubElement(phone, 'accountindex').text = '1'

    # Создаем элемент Groups и его подэлемент
    groups = ET.SubElement(contact, 'Groups')
    ET.SubElement(groups, 'groupid').text = '0'  # Можно изменить, если нужно

# Создаем дерево XML и записываем его в файл
tree = ET.ElementTree(root)
tree.write('addressbook.xml', pretty_print=True, xml_declaration=True, encoding='UTF-8')
