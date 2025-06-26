import json
import xml.etree.ElementTree as ET

# Путь к XML-файлу
xml_file = "uz.xml"

# Парсинг XML
tree = ET.parse(xml_file)
root = tree.getroot()

# Результирующий список словарей
towns = []

# Проход по всем <town> элементам
for town in root.findall("town"):
    code = town.find("code").text
    name = town.find("name").text

    # Пропускаем, если что-то отсутствует
    if code is None or name is None:
        continue

    towns.append({"code_city": int(code), "code_name": name})

# Сохраняем в JSON
with open("uz.json", "w", encoding="utf-8") as f:
    json.dump(towns, f, ensure_ascii=False, indent=4)

print("Данные успешно сохранены в uz.json")
