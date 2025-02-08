# import base64

# import requests
# from requests.adapters import HTTPAdapter
# from requests.packages.urllib3.util.retry import Retry

# username = "resteqsp@gmail.com"
# password = "Q7Hd.ATGCc5$ym2"
# auth_string = f"{username}:{password}"
# base64_auth = base64.b64encode(auth_string.encode()).decode()


# # Заголовки запроса
# headers = {"Authorization": f"Basic {base64_auth}", "Content-Type": "application/json"}
# data = {"data": {}}

# # URL API
# api_url = "https://marketplace-api.emag.ro/api-3"

# # Отправляем тестовый запрос
# response = requests.get(f"{api_url}/category/read", headers=headers, timeout=30)

# # Вывод результата
# print(response.status_code)
# print(response.json())


# import base64
# import json

# import requests
# from requests.adapters import HTTPAdapter
# from urllib3.util.retry import Retry

# username = "resteqsp@gmail.com"
# password = "Q7Hd.ATGCc5$ym2"
# auth_string = f"{username}:{password}"
# base64_auth = base64.b64encode(auth_string.encode()).decode()

# headers = {"Authorization": f"Basic {base64_auth}", "Content-Type": "application/json"}

# data = {"data": {"currentPage": 1, "itemsPerPage": 10}}

# api_url = "https://marketplace-api.emag.ro/api-3"

# session = requests.Session()
# retry = Retry(connect=3, backoff_factor=0.5)
# adapter = HTTPAdapter(max_retries=retry)
# session.mount("http://", adapter)
# session.mount("https://", adapter)

# response = session.post(
#     f"{api_url}/category/read", headers=headers, json=data, timeout=30
# )

# # print(response.status_code)
# # print(response.json())

# with open("output_json_file.json", "w", encoding="utf-8") as json_file:
#     json.dump(response.json(), json_file, ensure_ascii=False, indent=4)


import base64
import json

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Данные для авторизации
username = "resteqsp@gmail.com"
password = "Q7Hd.ATGCc5$ym2"
auth_string = f"{username}:{password}"
base64_auth = base64.b64encode(auth_string.encode()).decode()

# Заголовки запроса
headers = {"Authorization": f"Basic {base64_auth}", "Content-Type": "application/json"}

api_url = "https://marketplace-api.emag.ro/api-3"
# Настройка сессии с повторными попытками
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)


def get_category():

    # Параметры пагинации
    current_page = 1
    items_per_page = 100  # Максимальное количество элементов на странице
    all_results = []

    while True:
        data = {"data": {"currentPage": current_page, "itemsPerPage": items_per_page}}

        response = session.post(
            f"{api_url}/category/read", headers=headers, json=data, timeout=30
        )

        if response.status_code != 200:
            print(f"Ошибка {response.status_code}: {response.text}")
            break

        response_data = response.json()

        if response_data.get("isError"):
            print(f"Ошибка API: {response_data.get('messages')}")
            break

        results = response_data.get("results", [])
        if not results:
            break  # Прекращаем, если больше нет данных

        all_results.extend(results)
        print(f"Загружено {len(all_results)} категорий...")

        current_page += 1

    # Сохранение всех данных в файл
    with open("output_json_file.json", "w", encoding="utf-8") as json_file:
        json.dump(all_results, json_file, ensure_ascii=False, indent=4)

    print(f"Всего загружено {len(all_results)} категорий")


def calculate_ean13_checksum(ean12):
    """
    Вычисляет контрольную сумму для EAN-13
    """
    total = 0
    for i in range(12):
        digit = int(ean12[i])
        multiplier = 3 if i % 2 else 1
        total += digit * multiplier

    checksum = (10 - (total % 10)) % 10
    return f"{ean12}{checksum}"


def generate_valid_ean13():
    """
    Генерирует валидный EAN-13 код
    """
    # Используем фиксированный префикс для Польши (590)
    prefix = "590"
    # Добавляем уникальное число (например, на основе ID товара)
    middle = "000017006"  # Можно использовать часть ID товара
    ean12 = f"{prefix}{middle}"
    return calculate_ean13_checksum(ean12)


def product_offer_save():
    valid_ean = generate_valid_ean13()
    # Данные о товаре
    # Данные для загрузки товара
    # Данные товара согласно документации
    product_data = [
        {
            "id": 17006903216,
            "category_id": 2768,
            "part_number": "A8-1106-A7085",
            "name": "3,5-calowa konsola D22 HD Large Screen - przenośna gra zręcznościowa",
            "brand": "No brand",
            "description": '<section class="section"><div class="item item-6">Przenośna konsola do gier D22 HD z dużym ekranem 3,5 cala</div></section>',
            "url": "https://your-shop.com/A8-1106-A7085",
            "status": 1,
            "sale_price": 153.0,
            "vat_id": 4003,
            "warranty": 24,
            "images": [
                {
                    "display_type": 1,
                    "url": "https://a.allegroimg.com/original/11f445/fb5c4b654145925c3858619e016e/3-5-calowa-konsola-D22-HD-Large-Screen-prze",
                },
                {
                    "display_type": 0,
                    "url": "https://a.allegroimg.com/original/111315/be5dd0644ce4bc2ccbd5bcff81fc/3-5-calowa-konsola-D22-HD-Large-Screen-prze-Producent-bez-marki",
                },
                {
                    "display_type": 0,
                    "url": "https://a.allegroimg.com/original/11d23b/e9a4161e4849b21332d3add892e7/3-5-calowa-konsola-D22-HD-Large-Screen-prze-Kod-producenta-A8-1106-A7085",
                },
            ],
            "stock": [{"warehouse_id": 1, "value": 199}],
            "characteristics": [
                {"id": 9623, "value": "Maini"},  # Значение для Zona corporala (руки)
                {
                    "id": 5704,
                    "value": "Freza electrica",  # Значение для Tip produs (электрическая фреза)
                },
            ],
            "ean": [valid_ean],  # Добавлен уникальный EAN код
            "handling_time": [{"warehouse_id": 1, "value": 1}],
        }
    ]

    # Полный URL для загрузки товаров
    full_api_url = f"{api_url}/product_offer/save"

    # Отправка запроса через сессию
    response = session.post(
        full_api_url, headers=headers, json=product_data, timeout=30
    )

    # Проверка статуса ответа и вывод результата
    if response.status_code == 200:
        print("Товар успешно загружен!")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    else:
        print(f"Ошибка {response.status_code}: {response.text}")


def product_read():
    full_api_url = f"{api_url}/product_offer/read"
    product_data = {"data": {"currentPage": 1, "itemsPerPage": 100}}

    # Отправка запроса через сессию
    response = session.post(
        full_api_url, headers=headers, json=product_data, timeout=30
    )

    # Проверка статуса ответа и вывод результата
    if response.status_code == 200:
        print("Товар успешно загружен!")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
        # Сохранение всех данных в файл
        with open("output_json_priduct.json", "w", encoding="utf-8") as json_file:
            json.dump(response.json(), json_file, ensure_ascii=False, indent=4)
    else:
        print(f"Ошибка {response.status_code}: {response.text}")


if __name__ == "__main__":
    # Вызов функции для загрузки товара
    product_offer_save()
    # product_read()
