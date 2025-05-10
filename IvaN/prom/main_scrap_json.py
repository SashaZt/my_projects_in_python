import json
from pathlib import Path

from IvaN.prom.config.logger import logger

# Настройка директорий
current_directory = Path.cwd()
json_id_directory = current_directory / "json_id"
config_directory = current_directory / "config"
config_directory.mkdir(parents=True, exist_ok=True)
json_id_directory.mkdir(parents=True, exist_ok=True)


def scrap_json():
    all_data = []
    files = list(json_id_directory.glob("*.json"))
    # Пройтись по каждому HTML файлу в папке
    for json_file in files:
        with open(json_file, "r", encoding="utf-8") as file:
            input_data = json.load(file)
        logger.info(json_file)
        try:
            # Проверка 1: Убедимся, что input_data — словарь
            if not isinstance(input_data, dict):
                print("Ошибка: input_data не является словарем")
                return {}

            # Проверка 2: Безопасно извлекаем 'data' и 'company'
            data = input_data.get("data", {})
            if not isinstance(data, dict):
                print("Ошибка: 'data' не является словарем")
                return {}

            company_data = data.get("company", {})
            if not isinstance(company_data, dict):
                print("Ошибка: 'company' не является словарем")
                return {}

            # Извлекаем необходимые поля с безопасной обработкой

            result = {
                # Проверка 3: Извлечение 'id'
                "companyId": company_data.get("id"),
                # Проверка 4: Извлечение 'name' с очисткой от лишних символов
                "companyName": (
                    company_data.get("name").replace('"', "").replace("\\", "")
                    if company_data.get("name")
                    and isinstance(company_data.get("name"), str)
                    else None
                ),
                # Проверка 5: Извлечение простых полей
                "companyPerson": company_data.get("contactPerson"),
                "companyEmail": company_data.get("contactEmail"),
                "companyAddress": company_data.get("addressText"),
                "companySlug": company_data.get("slug"),
                "companyWebsite": company_data.get("webSiteUrl"),
                # Проверка 6: Извлечение 'phones' с очисткой номеров
                "companyPhones": (
                    [
                        phone.get("number")
                        .replace(" ", "")
                        .replace("(", "")
                        .replace(")", "")
                        .replace("-", "")
                        .replace('"', "")
                        for phone in company_data.get("phones", [])
                        if isinstance(phone, dict)
                        and phone.get("number")
                        and isinstance(phone.get("number"), str)
                    ]
                    if company_data.get("phones")
                    and isinstance(company_data.get("phones"), list)
                    else []
                ),
                # Проверка 7: Извлечение 'geoCoordinates' с вложенными полями
                "companyGeoCoordinates": (
                    {
                        "latitude": company_data.get("geoCoordinates", {}).get(
                            "latitude"
                        ),
                        "longtitude": company_data.get("geoCoordinates", {}).get(
                            "longtitude"
                        ),
                    }
                    if company_data.get("geoCoordinates")
                    and isinstance(company_data.get("geoCoordinates"), dict)
                    else None
                ),
            }

            all_data.append(result)
        except Exception as e:
            # Проверка 8: Перехват любых непредвиденных ошибок
            print(f"Ошибка при извлечении данных: {e}")
            return {}
    with open("result.json", "w", encoding="utf-8") as json_file:
        json.dump(all_data, json_file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    scrap_json()
