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


def product_offer_save():
    # Данные о товаре
    product_data = {
        "data": {
            "products": [
                {
                    "id": 95117032,
                    "category_id": 58,
                    "name": "Aspirator vertical, Roidmi, X20S",
                    "part_number": "D603G9MBM777",
                    "brand": "Roidmi",
                    "description": "<h2><strong>Aspirator vertical, Roidmi...</strong></h2>",
                    "images": [
                        "https://s13emagst.akamaized.net/products/42426/42425604/images/res_d59ae9024bc69d4a12b81e02f248ab80.jpg"
                    ],
                    "sale_price": 1558.99,
                    "min_sale_price": 1400.00,
                    "max_sale_price": 1700.00,
                    "currency": "RON",
                    "vat_id": 1,
                    "stock": [{"warehouse_id": 1, "value": 10}],
                    "status": 1,
                    "ean": ["1234567890123"],
                    "specifications": {
                        "Tip produs": "Aspirator vertical cu spalare",
                        "Putere": "435 W",
                        "Greutate": "1.5 Kg",
                    },
                }
            ]
        }
    }

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


if __name__ == "__main__":
    # Вызов функции для загрузки товара
    product_offer_save()
