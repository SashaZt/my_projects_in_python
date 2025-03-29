# policy_management.py
"""
Модуль для управления политиками продавца на eBay (оплата, доставка, возврат).
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from inventory_client import EbayInventoryClient
from logger import logger

from config import DEFAULT_MARKETPLACE_ID

current_directory = Path.cwd()
policy_directory = current_directory / "policy"
policy_directory.mkdir(parents=True, exist_ok=True)
payment_policy_file_path = policy_directory / "payment_policy.json"
return_policy_file_path = policy_directory / "return_policy.json"
fulfillment_policy_file_path = policy_directory / "fulfillment_policy.json"


def load_policy_data(json_file: str) -> Dict[str, Any]:
    """Загрузка данных политики из JSON-файла"""
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        logger.error(f"Файл {json_file} не найден.")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Ошибка декодирования JSON в файле {json_file}.")
        return {}


def save_policy_ids(policy_ids: Dict[str, str]) -> bool:
    """Сохранение ID политик в JSON-файл"""
    config_dir = "config"
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    config_file = os.path.join(config_dir, "policy_ids.json")

    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(policy_ids, f, indent=4)
        logger.info(f"ID политик сохранены в файл {config_file}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении ID политик: {e}")
        return False


def get_policy_ids() -> Dict[str, str]:
    """Получение сохраненных ID политик из файла"""
    config_file = "config/policy_ids.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка при чтении файла {config_file}: {e}")

    return {}


def create_payment_policy(
    payment_data: Optional[Dict[str, Any]] = None,
) -> Union[Dict[str, Any], None]:
    """
    Создание политики оплаты

    Args:
        payment_data (Dict[str, Any], optional): Данные для политики оплаты

    Returns:
        Union[Dict[str, Any], None]: Результат создания политики или None в случае ошибки
    """
    logger.info("Создание политики оплаты...")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return None

    # Используем данные из параметра или загружаем из файла
    if not payment_data:
        payment_data = load_policy_data(payment_policy_file_path)
        if not payment_data:
            logger.error("Не удалось загрузить данные политики оплаты")
            return None

    # Заменяем маркетплейс на актуальный
    payment_data["marketplaceId"] = DEFAULT_MARKETPLACE_ID

    # Выполняем запрос на создание политики
    endpoint = "sell/account/v1/payment_policy"
    result = client._call_api(endpoint, "POST", data=payment_data)

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при создании политики оплаты: {result['errors']}")
        return None

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при создании политики оплаты: {result['error']}")
        return None

    # Сохраняем ID политики
    if isinstance(result, dict) and "paymentPolicyId" in result:
        policy_id = result["paymentPolicyId"]
        logger.info(f"Политика оплаты успешно создана, ID: {policy_id}")

        # Обновляем сохраненные ID политик
        policy_ids = get_policy_ids()
        policy_ids["PAYMENT_POLICY_ID"] = policy_id
        save_policy_ids(policy_ids)

        return result

    logger.error("Не удалось получить ID политики оплаты из ответа API")
    return None


def create_return_policy(
    return_data: Optional[Dict[str, Any]] = None,
) -> Union[Dict[str, Any], None]:
    """
    Создание политики возврата

    Args:
        return_data (Dict[str, Any], optional): Данные для политики возврата

    Returns:
        Union[Dict[str, Any], None]: Результат создания политики или None в случае ошибки
    """
    logger.info("Создание политики возврата...")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return None

    # Используем данные из параметра или загружаем из файла
    if not return_data:
        return_data = load_policy_data(return_policy_file_path)
        if not return_data:
            logger.error("Не удалось загрузить данные политики возврата")
            return None

    # Заменяем маркетплейс на актуальный
    return_data["marketplaceId"] = DEFAULT_MARKETPLACE_ID

    # Выполняем запрос на создание политики
    endpoint = "sell/account/v1/return_policy"
    result = client._call_api(endpoint, "POST", data=return_data)

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при создании политики возврата: {result['errors']}")
        return None

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при создании политики возврата: {result['error']}")
        return None

    # Сохраняем ID политики
    if isinstance(result, dict) and "returnPolicyId" in result:
        policy_id = result["returnPolicyId"]
        logger.info(f"Политика возврата успешно создана, ID: {policy_id}")

        # Обновляем сохраненные ID политик
        policy_ids = get_policy_ids()
        policy_ids["RETURN_POLICY_ID"] = policy_id
        save_policy_ids(policy_ids)

        return result

    logger.error("Не удалось получить ID политики возврата из ответа API")
    return None


def create_fulfillment_policy(
    fulfillment_data: Optional[Dict[str, Any]] = None,
) -> Union[Dict[str, Any], None]:
    """
    Создание политики доставки

    Args:
        fulfillment_data (Dict[str, Any], optional): Данные для политики доставки

    Returns:
        Union[Dict[str, Any], None]: Результат создания политики или None в случае ошибки
    """
    logger.info("Создание политики доставки...")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return None

    # Используем данные из параметра или загружаем из файла
    if not fulfillment_data:
        fulfillment_data = load_policy_data(fulfillment_policy_file_path)
        if not fulfillment_data:
            logger.error("Не удалось загрузить данные политики доставки")
            return None

    # Заменяем маркетплейс на актуальный
    fulfillment_data["marketplaceId"] = DEFAULT_MARKETPLACE_ID

    # Выполняем запрос на создание политики
    endpoint = "sell/account/v1/fulfillment_policy"
    result = client._call_api(endpoint, "POST", data=fulfillment_data)

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при создании политики доставки: {result['errors']}")
        return None

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при создании политики доставки: {result['error']}")
        return None

    # Сохраняем ID политики
    if isinstance(result, dict) and "fulfillmentPolicyId" in result:
        policy_id = result["fulfillmentPolicyId"]
        logger.info(f"Политика доставки успешно создана, ID: {policy_id}")

        # Обновляем сохраненные ID политик
        policy_ids = get_policy_ids()
        policy_ids["SHIPPING_POLICY_ID"] = policy_id
        save_policy_ids(policy_ids)

        return result

    logger.error("Не удалось получить ID политики доставки из ответа API")
    return None


def update_payment_policy(policy_id: str, update_data: Dict[str, Any]) -> bool:
    """
    Обновление политики оплаты

    Args:
        policy_id (str): ID политики оплаты
        update_data (Dict[str, Any]): Данные для обновления

    Returns:
        bool: Результат операции
    """
    logger.info(f"Обновление политики оплаты с ID: {policy_id}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    # Получаем текущую политику
    current_policy = get_payment_policy(policy_id)
    if not current_policy:
        logger.error(f"Не удалось получить текущую политику оплаты с ID: {policy_id}")
        return False

    # Обновляем данные политики
    for key, value in update_data.items():
        if key in current_policy:
            if isinstance(value, dict) and isinstance(current_policy[key], dict):
                # Рекурсивно обновляем вложенные словари
                current_policy[key].update(value)
            else:
                current_policy[key] = value
        else:
            current_policy[key] = value

    # Выполняем запрос на обновление политики
    endpoint = f"sell/account/v1/payment_policy/{policy_id}"
    result = client._call_api(endpoint, "PUT", data=current_policy)

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при обновлении политики оплаты: {result['errors']}")
        return False

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при обновлении политики оплаты: {result['error']}")
        return False

    logger.info(f"Политика оплаты успешно обновлена: {policy_id}")
    return True


def update_return_policy(policy_id: str, update_data: Dict[str, Any]) -> bool:
    """
    Обновление политики возврата

    Args:
        policy_id (str): ID политики возврата
        update_data (Dict[str, Any]): Данные для обновления

    Returns:
        bool: Результат операции
    """
    logger.info(f"Обновление политики возврата с ID: {policy_id}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    # Получаем текущую политику
    current_policy = get_return_policy(policy_id)
    if not current_policy:
        logger.error(f"Не удалось получить текущую политику возврата с ID: {policy_id}")
        return False

    # Обновляем данные политики
    for key, value in update_data.items():
        if key in current_policy:
            if isinstance(value, dict) and isinstance(current_policy[key], dict):
                # Рекурсивно обновляем вложенные словари
                current_policy[key].update(value)
            else:
                current_policy[key] = value
        else:
            current_policy[key] = value

    # Выполняем запрос на обновление политики
    endpoint = f"sell/account/v1/return_policy/{policy_id}"
    result = client._call_api(endpoint, "PUT", data=current_policy)

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при обновлении политики возврата: {result['errors']}")
        return False

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при обновлении политики возврата: {result['error']}")
        return False

    logger.info(f"Политика возврата успешно обновлена: {policy_id}")
    return True


def update_fulfillment_policy(policy_id: str, update_data: Dict[str, Any]) -> bool:
    """
    Обновление политики доставки

    Args:
        policy_id (str): ID политики доставки
        update_data (Dict[str, Any]): Данные для обновления

    Returns:
        bool: Результат операции
    """
    logger.info(f"Обновление политики доставки с ID: {policy_id}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    # Получаем текущую политику
    current_policy = get_fulfillment_policy(policy_id)
    if not current_policy:
        logger.error(f"Не удалось получить текущую политику доставки с ID: {policy_id}")
        return False

    # Обновляем данные политики
    for key, value in update_data.items():
        if key in current_policy:
            if isinstance(value, dict) and isinstance(current_policy[key], dict):
                # Рекурсивно обновляем вложенные словари
                current_policy[key].update(value)
            else:
                current_policy[key] = value
        else:
            current_policy[key] = value

    # Выполняем запрос на обновление политики
    endpoint = f"sell/account/v1/fulfillment_policy/{policy_id}"
    result = client._call_api(endpoint, "PUT", data=current_policy)

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при обновлении политики доставки: {result['errors']}")
        return False

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при обновлении политики доставки: {result['error']}")
        return False

    logger.info(f"Политика доставки успешно обновлена: {policy_id}")
    return True


def get_payment_policy(policy_id: str) -> Union[Dict[str, Any], None]:
    """
    Получение информации о политике оплаты по ID

    Args:
        policy_id (str): ID политики оплаты

    Returns:
        Union[Dict[str, Any], None]: Данные политики или None в случае ошибки
    """
    logger.info(f"Получение информации о политике оплаты с ID: {policy_id}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return None

    endpoint = f"sell/account/v1/payment_policy/{policy_id}"
    result = client._call_api(endpoint, "GET")

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при получении политики оплаты: {result['errors']}")
        return None

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при получении политики оплаты: {result['error']}")
        return None

    return result


def get_return_policy(policy_id: str) -> Union[Dict[str, Any], None]:
    """
    Получение информации о политике возврата по ID

    Args:
        policy_id (str): ID политики возврата

    Returns:
        Union[Dict[str, Any], None]: Данные политики или None в случае ошибки
    """
    logger.info(f"Получение информации о политике возврата с ID: {policy_id}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return None

    endpoint = f"sell/account/v1/return_policy/{policy_id}"
    result = client._call_api(endpoint, "GET")

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при получении политики возврата: {result['errors']}")
        return None

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при получении политики возврата: {result['error']}")
        return None

    return result


def get_fulfillment_policy(policy_id: str) -> Union[Dict[str, Any], None]:
    """
    Получение информации о политике доставки по ID

    Args:
        policy_id (str): ID политики доставки

    Returns:
        Union[Dict[str, Any], None]: Данные политики или None в случае ошибки
    """
    logger.info(f"Получение информации о политике доставки с ID: {policy_id}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return None

    endpoint = f"sell/account/v1/fulfillment_policy/{policy_id}"
    result = client._call_api(endpoint, "GET")

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при получении политики доставки: {result['errors']}")
        return None

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при получении политики доставки: {result['error']}")
        return None

    return result


def delete_payment_policy(policy_id: str) -> bool:
    """
    Удаление политики оплаты

    Args:
        policy_id (str): ID политики оплаты

    Returns:
        bool: Результат операции
    """
    logger.info(f"Удаление политики оплаты с ID: {policy_id}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    endpoint = f"sell/account/v1/payment_policy/{policy_id}"
    result = client._call_api(endpoint, "DELETE")

    # Успешное удаление возвращает пустой ответ с кодом 204
    if result is None or (isinstance(result, dict) and not result):
        logger.info(f"Политика оплаты успешно удалена: {policy_id}")

        # Обновляем сохраненные ID политик
        policy_ids = get_policy_ids()
        if "PAYMENT_POLICY_ID" in policy_ids:
            del policy_ids["PAYMENT_POLICY_ID"]
            save_policy_ids(policy_ids)

        return True

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при удалении политики оплаты: {result['errors']}")
        return False

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при удалении политики оплаты: {result['error']}")
        return False

    logger.info(f"Политика оплаты успешно удалена: {policy_id}")
    return True


def delete_return_policy(policy_id: str) -> bool:
    """
    Удаление политики возврата

    Args:
        policy_id (str): ID политики возврата

    Returns:
        bool: Результат операции
    """
    logger.info(f"Удаление политики возврата с ID: {policy_id}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    endpoint = f"sell/account/v1/return_policy/{policy_id}"
    result = client._call_api(endpoint, "DELETE")

    # Успешное удаление возвращает пустой ответ с кодом 204
    if result is None or (isinstance(result, dict) and not result):
        logger.info(f"Политика возврата успешно удалена: {policy_id}")

        # Обновляем сохраненные ID политик
        policy_ids = get_policy_ids()
        if "RETURN_POLICY_ID" in policy_ids:
            del policy_ids["RETURN_POLICY_ID"]
            save_policy_ids(policy_ids)

        return True

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при удалении политики возврата: {result['errors']}")
        return False

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при удалении политики возврата: {result['error']}")
        return False

    logger.info(f"Политика возврата успешно удалена: {policy_id}")
    return True


def delete_fulfillment_policy(policy_id: str) -> bool:
    """
    Удаление политики доставки

    Args:
        policy_id (str): ID политики доставки

    Returns:
        bool: Результат операции
    """
    logger.info(f"Удаление политики доставки с ID: {policy_id}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    endpoint = f"sell/account/v1/fulfillment_policy/{policy_id}"
    result = client._call_api(endpoint, "DELETE")

    # Успешное удаление возвращает пустой ответ с кодом 204
    if result is None or (isinstance(result, dict) and not result):
        logger.info(f"Политика доставки успешно удалена: {policy_id}")

        # Обновляем сохраненные ID политик
        policy_ids = get_policy_ids()
        if "SHIPPING_POLICY_ID" in policy_ids:
            del policy_ids["SHIPPING_POLICY_ID"]
            save_policy_ids(policy_ids)

        return True

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при удалении политики доставки: {result['errors']}")
        return False

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при удалении политики доставки: {result['error']}")
        return False

    logger.info(f"Политика доставки успешно удалена: {policy_id}")
    return True


def get_all_payment_policies() -> List[Dict[str, Any]]:
    """
    Получение всех политик оплаты

    Returns:
        List[Dict[str, Any]]: Список политик оплаты
    """
    logger.info("Получение списка политик оплаты...")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return []

    endpoint = f"sell/account/v1/payment_policy?marketplace_id={DEFAULT_MARKETPLACE_ID}"
    result = client._call_api(endpoint, "GET")

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при получении политик оплаты: {result['errors']}")
        return []

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при получении политик оплаты: {result['error']}")
        return []

    if isinstance(result, dict) and "paymentPolicies" in result:
        policies = result.get("paymentPolicies", [])
        logger.info(f"Получено политик оплаты: {len(policies)}")
        return policies

    logger.error("Не удалось получить список политик оплаты")
    return []


def get_all_return_policies() -> List[Dict[str, Any]]:
    """
    Получение всех политик возврата

    Returns:
        List[Dict[str, Any]]: Список политик возврата
    """
    logger.info("Получение списка политик возврата...")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return []

    endpoint = f"sell/account/v1/return_policy?marketplace_id={DEFAULT_MARKETPLACE_ID}"

    result = client._call_api(endpoint, "GET")

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при получении политик возврата: {result['errors']}")
        return []

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при получении политик возврата: {result['error']}")
        return []

    if isinstance(result, dict) and "returnPolicies" in result:
        policies = result.get("returnPolicies", [])
        logger.info(f"Получено политик возврата: {len(policies)}")
        return policies

    logger.error("Не удалось получить список политик возврата")
    return []


def get_all_fulfillment_policies() -> List[Dict[str, Any]]:
    """
    Получение всех политик доставки

    Returns:
        List[Dict[str, Any]]: Список политик доставки
    """
    logger.info("Получение списка политик доставки...")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return []

    endpoint = (
        f"sell/account/v1/fulfillment_policy?marketplace_id={DEFAULT_MARKETPLACE_ID}"
    )

    result = client._call_api(endpoint, "GET")

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при получении политик доставки: {result['errors']}")
        return []

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при получении политик доставки: {result['error']}")
        return []

    if isinstance(result, dict) and "fulfillmentPolicies" in result:
        policies = result.get("fulfillmentPolicies", [])
        logger.info(f"Получено политик доставки: {len(policies)}")
        return policies

    logger.error("Не удалось получить список политик доставки")
    return []


def create_all_policies() -> bool:
    """
    Создание всех типов политик (оплата, возврат, доставка)

    Returns:
        bool: Результат операции
    """
    logger.info("Создание всех типов политик...")

    # Загружаем данные для политик
    payment_data = load_policy_data(payment_policy_file_path)
    return_data = load_policy_data(return_policy_file_path)
    fulfillment_data = load_policy_data(fulfillment_policy_file_path)

    # Проверяем наличие данных
    if not payment_data or not return_data or not fulfillment_data:
        logger.error("Не удалось загрузить данные для всех типов политик")
        return False

    # Создаем политики
    payment_result = create_payment_policy(payment_data)
    return_result = create_return_policy(return_data)
    fulfillment_result = create_fulfillment_policy(fulfillment_data)

    # Проверяем результаты
    success = bool(payment_result and return_result and fulfillment_result)

    if success:
        logger.info("Все типы политик успешно созданы")
    else:
        logger.error("Не удалось создать все типы политик")

    return success


def main():
    """Основная функция для работы с политиками"""
    print("=== Управление политиками на eBay ===")
    print("1. Создать все типы политик")
    print("2. Получить список всех политик")
    print("3. Создать политику оплаты")
    print("4. Создать политику возврата")
    print("5. Создать политику доставки")
    print("6. Удалить политику оплаты")
    print("7. Удалить политику возврата")
    print("8. Удалить политику доставки")
    print("0. Выход")

    choice = input("Выберите действие: ")

    if choice == "1":
        if create_all_policies():
            print("Все типы политик успешно созданы")
        else:
            print("Не удалось создать все типы политик")

    elif choice == "2":
        print("=== Политики оплаты ===")
        payment_policies = get_all_payment_policies()
        if payment_policies:
            for i, policy in enumerate(payment_policies, 1):
                policy_id = policy.get("paymentPolicyId", "Н/Д")
                name = policy.get("name", "Без названия")
                marketplace = policy.get("marketplaceId", "Н/Д")
                print(
                    f"{i}. ID: {policy_id}, Название: {name}, Маркетплейс: {marketplace}"
                )
        else:
            print("Политики оплаты не найдены или произошла ошибка")

        print("\n=== Политики возврата ===")
        return_policies = get_all_return_policies()
        if return_policies:
            for i, policy in enumerate(return_policies, 1):
                policy_id = policy.get("returnPolicyId", "Н/Д")
                name = policy.get("name", "Без названия")
                marketplace = policy.get("marketplaceId", "Н/Д")
                print(
                    f"{i}. ID: {policy_id}, Название: {name}, Маркетплейс: {marketplace}"
                )
        else:
            print("Политики возврата не найдены или произошла ошибка")

        print("\n=== Политики доставки ===")
        fulfillment_policies = get_all_fulfillment_policies()
        if fulfillment_policies:
            for i, policy in enumerate(fulfillment_policies, 1):
                policy_id = policy.get("fulfillmentPolicyId", "Н/Д")
                name = policy.get("name", "Без названия")
                marketplace = policy.get("marketplaceId", "Н/Д")
                print(
                    f"{i}. ID: {policy_id}, Название: {name}, Маркетплейс: {marketplace}"
                )
        else:
            print("Политики доставки не найдены или произошла ошибка")

    elif choice == "3":

        payment_data = load_policy_data(payment_policy_file_path)
        if not payment_data:
            print("Не удалось загрузить данные политики оплаты из файла")
            return

        # Предоставляем возможность редактировать данные
        print(f"Текущее название политики: {payment_data.get('name', 'Не задано')}")
        new_name = input(
            "Введите новое название (или нажмите Enter для сохранения текущего): "
        )
        if new_name:
            payment_data["name"] = new_name

        print(
            f"Текущее описание политики: {payment_data.get('description', 'Не задано')}"
        )
        new_description = input(
            "Введите новое описание (или нажмите Enter для сохранения текущего): "
        )
        if new_description:
            payment_data["description"] = new_description

        # Применяем изменения
        result = create_payment_policy(payment_data)
        if result:
            print(
                f"Политика оплаты успешно создана, ID: {result.get('paymentPolicyId')}"
            )
        else:
            print("Не удалось создать политику оплаты")

    elif choice == "4":

        return_data = load_policy_data(return_policy_file_path)
        if not return_data:
            print("Не удалось загрузить данные политики возврата из файла")
            return

        # Предоставляем возможность редактировать данные
        print(f"Текущее название политики: {return_data.get('name', 'Не задано')}")
        new_name = input(
            "Введите новое название (или нажмите Enter для сохранения текущего): "
        )
        if new_name:
            return_data["name"] = new_name

        print(
            f"Текущее описание политики: {return_data.get('description', 'Не задано')}"
        )
        new_description = input(
            "Введите новое описание (или нажмите Enter для сохранения текущего): "
        )
        if new_description:
            return_data["description"] = new_description

        # Применяем изменения
        result = create_return_policy(return_data)
        if result:
            print(
                f"Политика возврата успешно создана, ID: {result.get('returnPolicyId')}"
            )
        else:
            print("Не удалось создать политику возврата")

    elif choice == "5":

        fulfillment_data = load_policy_data(fulfillment_policy_file_path)
        if not fulfillment_data:
            print("Не удалось загрузить данные политики доставки из файла")
            return

        # Предоставляем возможность редактировать данные
        print(f"Текущее название политики: {fulfillment_data.get('name', 'Не задано')}")
        new_name = input(
            "Введите новое название (или нажмите Enter для сохранения текущего): "
        )
        if new_name:
            fulfillment_data["name"] = new_name

        print(
            f"Текущее описание политики: {fulfillment_data.get('description', 'Не задано')}"
        )
        new_description = input(
            "Введите новое описание (или нажмите Enter для сохранения текущего): "
        )
        if new_description:
            fulfillment_data["description"] = new_description

        # Применяем изменения
        result = create_fulfillment_policy(fulfillment_data)
        if result:
            print(
                f"Политика доставки успешно создана, ID: {result.get('fulfillmentPolicyId')}"
            )
        else:
            print("Не удалось создать политику доставки")

    elif choice == "6":
        policy_id = input("Введите ID политики оплаты для удаления: ")
        confirm = input(
            f"Вы уверены, что хотите удалить политику оплаты с ID '{policy_id}'? (y/n): "
        )

        if confirm.lower() == "y":
            if delete_payment_policy(policy_id):
                print(f"Политика оплаты успешно удалена: {policy_id}")
            else:
                print("Не удалось удалить политику оплаты")
        else:
            print("Операция отменена")

    elif choice == "7":
        policy_id = input("Введите ID политики возврата для удаления: ")
        confirm = input(
            f"Вы уверены, что хотите удалить политику возврата с ID '{policy_id}'? (y/n): "
        )

        if confirm.lower() == "y":
            if delete_return_policy(policy_id):
                print(f"Политика возврата успешно удалена: {policy_id}")
            else:
                print("Не удалось удалить политику возврата")
        else:
            print("Операция отменена")

    elif choice == "8":
        policy_id = input("Введите ID политики доставки для удаления: ")
        confirm = input(
            f"Вы уверены, что хотите удалить политику доставки с ID '{policy_id}'? (y/n): "
        )

        if confirm.lower() == "y":
            if delete_fulfillment_policy(policy_id):
                print(f"Политика доставки успешно удалена: {policy_id}")
            else:
                print("Не удалось удалить политику доставки")
        else:
            print("Операция отменена")

    else:
        print("Выход из программы")


if __name__ == "__main__":
    main()
