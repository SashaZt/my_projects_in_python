import json
import logging

from api_client import EbayApiClient
from auth import EbayAuth
from logger import logger

from config import CLIENT_ID, CLIENT_SECRET


def test_available_apis(client):
    """Тестирование доступных API endpoints"""
    logger.info("Тестирование доступных API endpoints...")

    # Список эндпоинтов для тестирования
    endpoints = [
        (
            "commerce/taxonomy/v1/get_default_category_tree_id?marketplace_id=EBAY_DE",
            "GET",
        ),
        ("commerce/taxonomy/v1/category_tree/0", "GET"),
        ("buy/browse/v1/item_summary/search?q=laptop&limit=1", "GET"),
        (
            "buy/marketing/v1/merchandised_product?category_id=77&metric_name=BEST_SELLING",
            "GET",
        ),
    ]

    for endpoint, method in endpoints:
        logger.info(f"Тестирование {method} {endpoint}...")
        response = client._call_api(endpoint, method)
        if response:
            logger.info(f"✅ {method} {endpoint} - успешно")
            logger.info(f"Получены ключи: {list(response.keys())}")
        else:
            logger.error(f"❌ {method} {endpoint} - неудачно")


def extract_categories(node, parent_id=None, level=0):
    """Рекурсивное извлечение категорий из дерева"""
    result = []

    # Получение информации о текущей категории
    if "category" in node:
        category = node["category"]
        category_id = category.get("categoryId")
        category_name = category.get("categoryName")

        # Создание объекта категории
        category_info = {
            "id": category_id,
            "name": category_name,
            "parentId": parent_id,
            "level": level,
            "isLeaf": not node.get("childCategoryTreeNodes"),
        }

        result.append(category_info)

        # Рекурсивное извлечение дочерних категорий
        if "childCategoryTreeNodes" in node and node["childCategoryTreeNodes"]:
            for child_node in node["childCategoryTreeNodes"]:
                child_categories = extract_categories(
                    child_node, category_id, level + 1
                )
                result.extend(child_categories)

    return result


def get_all_categories():
    """Получение всех категорий eBay Германия"""
    # Инициализация авторизации и клиента API
    auth = EbayAuth()
    client = EbayApiClient(auth)

    # Получение ID дерева категорий для Германии
    logger.info("Получение ID дерева категорий для Германии...")
    category_tree_id = client.get_default_category_tree_id("EBAY_DE")
    logger.info(f"ID дерева категорий для Германии: {category_tree_id}")

    # Получение полного дерева категорий
    logger.info("Получение полного дерева категорий...")
    tree_data = client.get_category_tree(category_tree_id)

    # Проверка успешности получения дерева категорий
    if not tree_data or "rootCategoryNode" not in tree_data:
        logger.error("Не удалось получить дерево категорий")
        return None

    # Извлечение всех категорий из дерева
    root_node = tree_data["rootCategoryNode"]
    all_categories = extract_categories(root_node)

    logger.info(f"Извлечено {len(all_categories)} категорий")

    # Возвращение результата
    return {
        "categoryTreeId": category_tree_id,
        "categoryTreeVersion": tree_data.get("categoryTreeVersion"),
        "totalCategories": len(all_categories),
        "categories": all_categories,
    }


def save_categories_to_json(filename="ebay_de_categories.json"):
    """Сохранение всех категорий eBay Германия в JSON-файл"""
    categories_data = get_all_categories()

    if not categories_data:
        logger.error("Нет данных для сохранения")
        return False

    # Сохранение данных в JSON-файл
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(categories_data, file, ensure_ascii=False, indent=2)

    logger.info(
        f"Данные о {categories_data['totalCategories']} категориях сохранены в файл {filename}"
    )
    return True


def print_category_stats(categories_data):
    """Вывод статистики по категориям"""
    if not categories_data:
        logger.warning("Нет данных о категориях")
        return

    # Подсчет категорий по уровням
    levels = {}
    leaf_count = 0

    for category in categories_data["categories"]:
        level = category["level"]
        if level not in levels:
            levels[level] = 0
        levels[level] += 1

        if category["isLeaf"]:
            leaf_count += 1

    # Вывод статистики
    logger.info(f"Статистика категорий eBay Германия:")
    logger.info(f"Всего категорий: {categories_data['totalCategories']}")
    logger.info(f"Листовых категорий: {leaf_count}")

    # Вывод распределения по уровням
    logger.info("Распределение по уровням:")
    for level in sorted(levels.keys()):
        logger.info(f"  Уровень {level}: {levels[level]} категорий")

    # Вывод первых категорий каждого уровня для примера
    logger.info("Примеры категорий:")
    for level in sorted(levels.keys()):
        examples = [c for c in categories_data["categories"] if c["level"] == level][:3]
        logger.info(f"  Уровень {level}:")
        for example in examples:
            logger.info(f"    ID: {example['id']}, Имя: {example['name']}")


def process_category_aspects(category_id, marketplace_id="EBAY_DE"):
    auth = EbayAuth(CLIENT_ID, CLIENT_SECRET)
    client = EbayApiClient(auth)

    # Получение categoryTreeId
    category_tree_id = client.get_default_category_tree_id(marketplace_id)
    if not category_tree_id:
        logger.error("Не удалось получить ID дерева категорий")
        return None

    # Запрос аспектов
    endpoint = f"commerce/taxonomy/v1/category_tree/{category_tree_id}/get_item_aspects_for_category?category_id={category_id}"
    response = client._call_api(endpoint, "GET")
    if not response:
        logger.error(f"Не удалось получить аспекты для категории {category_id}")
        return None

    # Разделение на обязательные и необязательные аспекты
    aspects = response.get("aspects", [])
    required_aspects = [
        asp
        for asp in aspects
        if asp.get("aspectConstraint", {}).get("aspectRequired", False)
    ]
    optional_aspects = [
        asp
        for asp in aspects
        if not asp.get("aspectConstraint", {}).get("aspectRequired", False)
    ]

    # Вывод результатов
    logger.info(f"\nАспекты для категории {category_id} (EBAY_DE):")
    logger.info(f"Всего аспектов: {len(aspects)}")

    logger.info("\nОбязательные поля:")
    for asp in required_aspects:
        name = asp["localizedAspectName"]
        mode = asp["aspectConstraint"]["aspectMode"]
        values = [v["localizedValue"] for v in asp.get("aspectValues", [])][
            :5
        ]  # Первые 5 значений
        logger.info(f"- {name} ({mode})")
        if values:
            logger.info(f"  Примеры значений: {', '.join(values)}")

    logger.info("\nНеобязательные поля:")
    for asp in optional_aspects:
        name = asp["localizedAspectName"]
        mode = asp["aspectConstraint"]["aspectMode"]
        values = [v["localizedValue"] for v in asp.get("aspectValues", [])][
            :5
        ]  # Первые 5 значений
        logger.info(f"- {name} ({mode})")
        if values:
            logger.info(f"  Примеры значений: {', '.join(values)}")

    return response


def main():
    """Основная функция с примерами использования API eBay"""
    # Инициализация классов авторизации и клиента API
    auth = EbayAuth(CLIENT_ID, CLIENT_SECRET)
    client = EbayApiClient(auth)
    # Параметры для немецкого маркетплейса
    EBAY_GERMANY = "EBAY_DE"

    # Примеры использования API
    try:
        # # Добавьте вызов этой функции в main():
        # test_available_apis(client)
        #
        # # 1 Получение и сохранение категорий
        # categories_data = get_all_categories()

        # if categories_data:
        #     # Вывод статистики
        #     print_category_stats(categories_data)

        #     # Сохранение в JSON
        # save_categories_to_json()

        # # 1. Получение ID дерева категорий по умолчанию
        # logger.info(f"Получение ID дерева категорий для {EBAY_GERMANY}...")
        # category_tree_id = client.get_default_category_tree_id(EBAY_GERMANY)
        # logger.info(f"ID дерева категорий для Германии: {category_tree_id}")

        # # 2. Поиск предложений категорий
        # query = "laptop"
        # logger.info(f"Поиск категорий по запросу '{query}'...")
        # suggestions = client.get_category_suggestions(query, category_tree_id)
        # logger.info(f"Найдено {len(suggestions)} предложений категорий:")
        # for suggestion in suggestions[:5]:  # Выводим первые 5 предложений
        #     category = suggestion.get("category", {})
        #     logger.info(
        #         f"- {category.get('categoryName')} (ID: {category.get('categoryId')})"
        #     )

        # # 3. Поиск товаров
        # logger.info(f"Поиск товаров по запросу '{query}'...")
        # search_result = client.search_items(query, limit=10)
        # logger.info(f"Найдено {search_result.total} товаров")

        # # 4. Вывод результатов поиска
        # logger.info("Результаты поиска:")
        # for i, item in enumerate(
        #     search_result.items[:5], 1
        # ):  # Выводим первые 5 товаров
        #     logger.info(f"{i}. {item.title} - {item.price} {item.currency}")
        #     if item.listing_url:
        #         logger.info(f"   URL: {item.listing_url}")

        # # 5. Получение детальной информации о первом товаре
        # if search_result.items:
        #     first_item = search_result.items[0]
        #     logger.info(
        #         f"Получение детальной информации о товаре: {first_item.title}..."
        #     )
        #     item_details = client.get_item(first_item.item_id)
        #     logger.info("Детальная информация о товаре:")
        #     logger.info(f"- Название: {item_details.title}")
        #     logger.info(f"- Цена: {item_details.price} {item_details.currency}")
        #     logger.info(f"- Состояние: {item_details.condition}")
        #     logger.info(f"- Местоположение: {item_details.location}")
        #     if item_details.shipping_cost is not None:
        #         logger.info(
        #             f"- Стоимость доставки: {item_details.shipping_cost} {item_details.currency}"
        #         )
        #     logger.info(f"- Продавец: {item_details.seller_username}")
        #     if item_details.seller_feedback is not None:
        #         logger.info(f"- Рейтинг продавца: {item_details.seller_feedback}%")

        # # 6. Пример получения информации о дереве категорий
        # logger.info("Получение информации о дереве категорий...")
        # tree_info = client.get_category_tree(category_tree_id)
        # root_category = tree_info.get("rootCategoryNode", {})
        # logger.info(
        #     f"Корневая категория: {root_category.get('category', {}).get('categoryName')}"
        # )
        # child_categories = root_category.get("childCategoryTreeNodes", [])
        # logger.info(f"Количество дочерних категорий: {len(child_categories)}")
        # logger.info("Первые 5 дочерних категорий:")
        # for i, child in enumerate(child_categories[:5], 1):
        #     category = child.get("category", {})
        #     logger.info(
        #         f"{i}. {category.get('categoryName')} (ID: {category.get('categoryId')})"
        #     )
        category_id = "70432"  # Укажите ваш ID категории
        aspects_data = process_category_aspects(category_id)
        if aspects_data:
            with open(
                f"category_{category_id}_aspects.json", "w", encoding="utf-8"
            ) as file:
                json.dump(aspects_data, file, ensure_ascii=False, indent=2)
            logger.info(f"Данные сохранены в category_{category_id}_aspects.json")

    except Exception as e:
        logger.error(f"Ошибка во время выполнения: {e}")
        import traceback

        logger.error(traceback.format_exc())


def print_user_auth_instructions():
    """Вывод инструкций по авторизации пользователя"""
    auth = EbayAuth()
    auth_url = auth.get_authorization_url()

    logger.info("\n" + "=" * 80)
    logger.info("ИНСТРУКЦИИ ПО АВТОРИЗАЦИИ ПОЛЬЗОВАТЕЛЯ")
    logger.info("=" * 80)
    logger.info(
        "\nДля работы с методами API, требующими User токен, необходимо выполнить следующие шаги:"
    )
    logger.info("\n1. Настройте RuName в вашем аккаунте разработчика eBay:")
    logger.info("   - Войдите в аккаунт eBay Developer Program")
    logger.info("   - Перейдите в 'Your Account > Application Keys'")
    logger.info("   - Нажмите на 'User Tokens' рядом с Client ID")
    logger.info("   - Создайте и настройте RuName")

    if auth_url:
        logger.info(
            "\n2. После настройки RuName перейдите по следующей ссылке для авторизации пользователя:"
        )
        logger.info(f"   {auth_url}")
        logger.info(
            "\n3. После авторизации вы будете перенаправлены на указанный в RuName URL с кодом авторизации"
        )
        logger.info(
            "\n4. Скопируйте полученный код авторизации и используйте его для получения User токена:"
        )
        logger.info("   auth = EbayAuth()")
        logger.info("   auth.get_user_token(authorization_code)")
    else:
        logger.error(
            "\n2. После настройки RuName добавьте его в файл config.py и перезапустите скрипт"
        )

    logger.info("\n" + "=" * 80)


if __name__ == "__main__":
    # Запуск основной функции с примерами
    main()

    # Вывод инструкций по авторизации пользователя (если требуется User токен)
    # print_user_auth_instructions()
