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
# api_url = "https:#marketplace-api.emag.ro/api-3"

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

# api_url = "https:#marketplace-api.emag.ro/api-3"

# session = requests.Session()
# retry = Retry(connect=3, backoff_factor=0.5)
# adapter = HTTPAdapter(max_retries=retry)
# session.mount("http:#", adapter)
# session.mount("https:#", adapter)

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

api_url = "https:#marketplace-api.emag.ro/api-3"
# Настройка сессии с повторными попытками
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount("http:#", adapter)
session.mount("https:#", adapter)


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
    # Массив с данными о товаре для отправки в API
    product_data = [
        {
            "id": 1234567,  # Твой внутренний ID продукта
            "category_id": 1868,  # ID категории Treadmills
            "name": "Banda de alergat electrica FitTronic  D100",  # Название продукта
            "brand": "FitTronic",  # Бренд
            "part_number": "XR500-2023",  # Уникальный идентификатор продукта от производителя
            "description": "Cumpara Banda de alergat electrica FitTronic® D100, motor 2.5 CP, Bluetooth, Kinomap, Zwift, Newrunway, Self oil - ungere automata, sistem de amortizare in 6 puncte + arcuri, pliabila cu cilindru, intrare mp3 si USB pt muzica, cheie siguranta de la eMAG! Ai libertatea sa platesti in rate, beneficiezi de promotiile zilei, deschiderea coletului la livrare, easybox, retur gratuit in 30 de zile si Instant Money Back.",  # Описание
            "ean": ["1234567890123"],  # EAN код (обязательный для данной категории)
            "status": 1,  # 1 = активный
            "sale_price": 1999.99,  # Цена продажи без НДС
            "recommended_price": 2499.99,  # Рекомендованная цена (если есть скидка)
            "min_sale_price": 1899.99,  # Минимальная цена продажи
            "max_sale_price": 2599.99,  # Максимальная цена продажи
            "vat_id": 1,  # ID НДС (получи через /vat/read)
            "warranty": 24,  # Гарантия в месяцах
            "characteristics": [
                {
                    "id": 7764,  # Maximum supported weight (обязательная характеристика)
                    "value": "140 kg",
                },
                {
                    "id": 8147,  # Number of programs (обязательная характеристика)
                    "value": "12",
                },
                {
                    "id": 9080,  # Leg length (обязательная характеристика)
                    "value": "Standard",
                },
                {"id": 5401, "value": "Black"},  # Color
                {"id": 6779, "value": "130 cm"},  # Height
                {"id": 6780, "value": "85 cm"},  # Width
                {"id": 6862, "value": "180 cm"},  # Length
                {"id": 6878, "value": "120 kg"},  # Weight
                {"id": 7163, "value": "20 km/h"},  # Maximum speed
                {"id": 7442, "value": "2.5 HP"},  # Power engine
                {"id": 9082, "value": "Running"},  # Sport
                {"id": 9083, "value": "Professional"},  # Ability level
                {"id": 9275, "value": "Electric"},  # Incline type
                {"id": 9277, "value": "15"},  # Incline percentage
                {"id": 9280, "value": "20"},  # Levels of speed
                {"id": 9281, "value": "10"},  # Levels of incline
                {"id": 9282, "value": "0.5 km/h"},  # Minimum speed
                {"id": 9283, "value": "Yes"},  # Training computer
                {"id": 9286, "value": "500 x 1400"},  # Running surface
                {
                    "id": 9139,  # Functions
                    "value": "Heart rate monitor, Bluetooth, LCD display, Speakers",
                },
                {
                    "id": 8382,  # Measured values
                    "value": "Heart rate, Distance, Calories, Speed, Time",
                },
            ],
            "images": [
                {
                    "display_type": 1,  # 1 = главное изображение
                    "url": "https:#example.com/images/treadmill-main.jpg",
                },
                {
                    "display_type": 2,  # 2 = дополнительное изображение
                    "url": "https:#example.com/images/treadmill-side.jpg",
                },
                {
                    "display_type": 0,  # 0 = другое изображение
                    "url": "https:#example.com/images/treadmill-angle.jpg",
                },
            ],
            "stock": [{"warehouse_id": 1, "value": 10}],  # Количество на складе
            "handling_time": [
                {"warehouse_id": 1, "value": 2}  # Время обработки в днях
            ],
            "safety_information": "Перед использованием прочтите инструкцию. Не подходит для детей младше 14 лет.",
            "manufacturer": [
                {
                    "name": "FitnessExpert Manufacturing Ltd.",
                    "address": "123 Industrial Park, Manufacturing City, Country",
                    "email": "info@fitnessexpert-manufacturing.com",
                }
            ],
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
