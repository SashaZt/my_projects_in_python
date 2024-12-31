import xml.etree.ElementTree as ET
from xml.dom import minidom

property_data = {
    "status": "publish",
    "type": "property",
    "title": "Flat / apartment for sale in calle de Tòquio",
    "content": "<p>Описание объекта недвижимости...</p>",
    "excerpt": "<p>Краткое описание...</p>",
    "featured_media": 16124,  # Главное изображение
    "meta": {"fave_property_images": [{"id": "17548"}]},
}

# Создание корневого элемента
root = ET.Element("properties")

# Создание элемента property
property_elem = ET.SubElement(root, "property")

# Добавление простых атрибутов
for key, value in property_data.items():
    if key != "meta":
        ET.SubElement(property_elem, key).text = str(value)

# Добавление метаданных
meta = ET.SubElement(property_elem, "meta")
for meta_key, meta_value in property_data["meta"].items():
    meta_elem = ET.SubElement(meta, meta_key)
    if isinstance(meta_value, list):
        for item in meta_value:
            for inner_key, inner_value in item.items():
                ET.SubElement(meta_elem, inner_key).text = str(inner_value)

# Преобразование XML в строку для красивого вывода
xml_string = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")

# Сохранение XML в файл
with open("property_data.xml", "w", encoding="utf-8") as f:
    f.write(xml_string)

print("XML файл успешно сохранён как 'property_data.xml'.")
