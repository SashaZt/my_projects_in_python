import json
from datetime import datetime, timedelta
from pathlib import Path

import requests
from config.logger import logger

# # Загрузка переменных из .env
# env_path = os.path.join(os.getcwd(), "configuration", ".env")
# load_dotenv(env_path)
# IP = os.getenv("IP")
# FOLDER_ID = os.getenv("FOLDER_ID")
# SHEET_ID = os.getenv("SHEET_ID")
# API_KEY = os.getenv("API_KEY")
# GRAPHQL_URL = os.getenv("GRAPHQL_URL")
# SALESDRIVE_API = os.getenv("SALESDRIVE_API")
# client_gpt = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# # Заголовки для запроса
SALESDRIVE_API = "3m7xasIXKX7ME3TmEiN_CU2tajKMEtilHQ-smKeXnSFTKReKV2jEFn8J3TUoYC_aZa-dGQvC-c_NhV9Akl-gCTd-LfGT7v_dZlpe"
CRM_FORM_ID = (
    "_gidicYgNu5sO16suNI6gukV8Fi_YtNYglV0I1GWcQ9N5nGr7eW9ALUNkAeelRGLuTAMRCAPfhL"
)
current_directory = Path.cwd()
json_directory = current_directory / "json"
file_sajt = current_directory / "sajt.json"


def extract_and_save_sajt_options():
    """
    Функция для извлечения опций sajt из API и сохранения в файл
    """
    try:
        url = "https://zubr.salesdrive.me/api/order/list/"
        headers = {"Form-Api-Key": SALESDRIVE_API}
        params = {
            "page": 1,
            "limit": 1,  # Нужен только один результат для получения мета-данных
        }

        response = requests.get(url, headers=headers, params=params, timeout=(10, 30))

        if response.status_code == 200:
            data = response.json()

            # Извлекаем опции sajt из мета-данных
            sajt_options = (
                data.get("meta", {})
                .get("fields", {})
                .get("sajt", {})
                .get("options", [])
            )

            # Создаем массив словарей с value и text
            sajt_mapping = []
            for option in sajt_options:
                sajt_mapping.append(
                    {"value": option.get("value"), "text": option.get("text")}
                )

            # Сохраняем в файл
            with open(file_sajt, "w", encoding="utf-8") as f:
                json.dump(sajt_mapping, f, ensure_ascii=False, indent=4)

            logger.info(f"Сохранено {len(sajt_mapping)} опций sajt в файл sajt.json")
            return sajt_mapping

        else:
            logger.error(f"Ошибка при запросе: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Ошибка при извлечении опций sajt: {e}")
        return None


def load_sajt_options():
    """
    Загружает опции sajt из файла
    """
    try:
        if file_sajt.exists():
            with open(file_sajt, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            logger.error(
                "Файл sajt.json не найден. Сначала выполните extract_and_save_sajt_options()"
            )
            return None
    except Exception as e:
        logger.error(f"Ошибка при загрузке sajt.json: {e}")
        return None


def create_sajt_mapping_dict():
    """
    Создает словарь для быстрого поиска текста по значению
    """
    sajt_options = load_sajt_options()
    if sajt_options:
        return {option["value"]: option["text"] for option in sajt_options}
    return {}


def update_order_comments(orders_data):
    """
    Обновляет комментарии для списка заявок

    Args:
        orders_data (list): Список словарей с данными заявок

    Returns:
        list: Список результатов обновления для каждой заявки
    """
    results = []

    try:
        url = "https://zubr.salesdrive.me/api/order/update/"
        headers = {
            "Form-Api-Key": SALESDRIVE_API,
            "Content-Type": "application/json",
        }

        for order_data in orders_data:
            try:
                # logger.info(
                #     f"Отправляем запрос на обновление заявки {order_data['id']}"
                # )
                # Данные заказа для обновления
                order_id = order_data.get("id_order")
                order_sajt = order_data.get("order_sajt")
                payload = {
                    "form": CRM_FORM_ID,
                    "id": order_id,
                    "data": {
                        "sajt": order_sajt,
                    },
                }
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=(10, 30),  # (connect timeout, read timeout)
                )

                logger.info(f"Обновляем заявку в salesdrive {order_data["id"]}")

            except requests.exceptions.Timeout:
                logger.error(f"Timeout при запросе к API для заявки {order_data['id']}")
                results.append(
                    {
                        "id": order_data["id"],
                        "status": "error",
                        "error": "Timeout error",
                    }
                )
            except Exception as e:
                logger.error(f"Ошибка при обновлении заявки {order_data['id']}: {e}")
                results.append(
                    {"id": order_data["id"], "status": "error", "error": str(e)}
                )

    except Exception as e:
        logger.error(f"Критическая ошибка при обновлении заявок: {e}")
        raise

    return results


def get_salesdrive_orders(date_from=None, date_to=None):
    try:
        # Если даты не указаны, используем последние 24 часа
        if not date_from or not date_to:
            date_to = datetime.now()
            date_from = date_to - timedelta(days=1)
            date_to = date_to.replace(hour=23, minute=59, second=59)
            date_from = date_from.replace(hour=0, minute=0, second=0)

        # Форматируем даты
        date_from_str = date_from.strftime("%Y-%m-%d %H:%M:%S")
        date_to_str = date_to.strftime("%Y-%m-%d %H:%M:%S")

        url = "https://zubr.salesdrive.me/api/order/list/"
        headers = {"Form-Api-Key": SALESDRIVE_API}
        params = {
            "filter[orderTime][from]": date_from_str,
            "filter[orderTime][to]": date_to_str,
            "page": 1,
            "limit": 100,
        }

        response = requests.get(url, headers=headers, params=params, timeout=(10, 30))

        if response.status_code == 200:
            data = response.json()

            # Загружаем маппинг для sajt
            sajt_mapping = create_sajt_mapping_dict()
            matched_orders = []

            # Обрабатываем каждую заявку
            for order in data.get("data", []):
                original_sajt = order.get("sajt")
                id_order = order.get("id")

                # Проверяем, есть ли соответствие в маппинге
                if original_sajt is not None and has_sajt_mapping(original_sajt):
                    mapped_sajt = apply_sajt_mapping(original_sajt)

                    # Добавляем в результат только если есть соответствие
                    result = {
                        "id_order": id_order,
                        "original_sajt": original_sajt,
                        "mapped_sajt": mapped_sajt,
                    }
                    matched_orders.append(result)

                    # Для отладки
                    sajt_text = sajt_mapping.get(original_sajt, "Неизвестно")
                    logger.info(
                        f"Заявка {id_order}: sajt {original_sajt} ({sajt_text}) -> {mapped_sajt}"
                    )

            # Сохраняем результат в файл
            with open("matched_orders.json", "w", encoding="utf-8") as f:
                json.dump(matched_orders, f, ensure_ascii=False, indent=4)

            logger.info(
                f"Найдено {len(matched_orders)} заявок с соответствием в маппинге"
            )
            return matched_orders
        else:
            logger.error(f"Ошибка при получении заявок: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Ошибка при получении заявок: {e}")
        return None


def has_sajt_mapping(original_sajt):
    """
    Проверяет, есть ли соответствие в маппинге для данного sajt
    """
    mapping_rules = {
        48: 20,  # если sajt = 48, то заменить на 20
    }

    return original_sajt in mapping_rules


def apply_sajt_mapping(original_sajt):
    """
    Применяет маппинг для sajt значений
    Здесь ты можешь прописать свои правила
    """
    # Пример маппинга
    mapping_rules = {
        48: 20,  # если sajt = 48, то заменить на 20
    }

    return mapping_rules.get(original_sajt, original_sajt)


if __name__ == "__main__":
    extract_and_save_sajt_options()
    get_salesdrive_orders()
