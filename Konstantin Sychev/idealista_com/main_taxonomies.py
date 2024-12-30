import json

import requests

# Определяем базовый URL WordPress REST API
BASE_URL = "https://allproperty.ai/wp-json/wp/v2"
TOKEN_FILE = "token.json"  # Файл для сохранения токена


# Функция для получения данных из REST API
def fetch_taxonomy_data(taxonomy, token):
    url = f"{BASE_URL}/{taxonomy}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка получения данных для {taxonomy}: {response.text}")
        return []


# Главная функция для сохранения всех данных в JSON-файл
def save_all_taxonomies(token):
    taxonomies = [
        "property_type",
        "property_status",
        "property_feature",
        "property_label",
        "property_country",
        "property_state",
        "property_city",
        "property_area",
    ]

    all_data = {}

    for taxonomy in taxonomies:
        print(f"Получаем данные для: {taxonomy}...")
        data = fetch_taxonomy_data(taxonomy, token)
        all_data[taxonomy] = data

    # Сохранение данных в JSON-файл
    output_file = "property_taxonomies.json"
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(all_data, file, ensure_ascii=False, indent=4)

    print(f"Все данные таксономий сохранены в {output_file}")


# Пример использования
if __name__ == "__main__":
    with open(TOKEN_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
    token = data["token"]
    save_all_taxonomies(token)
