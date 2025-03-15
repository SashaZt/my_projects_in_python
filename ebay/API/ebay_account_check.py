# ebay_account_check.py
import json

import requests
from auth import EbayAuth
from logger import logger


def check_account_privileges():
    """
    Проверка привилегий аккаунта eBay в отношении различных API
    """
    # Инициализация авторизации
    auth = EbayAuth()

    # Проверка токена
    if not auth.user_token:
        logger.error("Не найден User токен. Необходима авторизация пользователя.")
        return False

    # Формируем заголовки запроса
    headers = {
        "Authorization": f"Bearer {auth.user_token['access_token']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    logger.info("=== Проверка привилегий аккаунта eBay ===")

    # Скоупы в токене
    if "scope" in auth.user_token:
        scopes = auth.user_token["scope"].split(" ")
        logger.info("Скоупы в текущем токене:")
        for scope in scopes:
            logger.info(f"  - {scope}")

        # Проверка наличия необходимых скоупов
        inventory_scopes = [
            "https://api.ebay.com/oauth/api_scope/sell.inventory",
            "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly",
        ]

        missing_scopes = [scope for scope in inventory_scopes if scope not in scopes]
        if missing_scopes:
            logger.error("⚠️ Отсутствуют следующие скоупы для Inventory API:")
            for scope in missing_scopes:
                logger.error(f"  - {scope}")
        else:
            logger.info("✅ Все необходимые скоупы для Inventory API присутствуют")

    # Проверка доступных API
    try:
        logger.info("\nПроверка доступа к основным API eBay:")

        # 1. Проверка Browse API
        try:
            logger.info("1. Проверка Browse API:")
            browse_url = f"{auth.token_storage.get_base_url()}/buy/browse/v1/item_summary/search?q=phone&limit=1"
            response = requests.get(browse_url, headers=headers, timeout=30)

            if response.status_code < 400:
                logger.info(f"  ✅ Browse API доступен: {response.status_code}")
            else:
                logger.warning(
                    f"  ❌ Ошибка доступа к Browse API: {response.status_code}"
                )
                try:
                    error_data = response.json()
                    logger.warning(f"  Ответ: {json.dumps(error_data, indent=2)}")
                except:
                    logger.warning(f"  Ответ (не JSON): {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при проверке Browse API: {e}")

        # 2. Проверка Inventory API - Items
        try:
            logger.info("2. Проверка Inventory API (Items):")
            items_url = f"{auth.token_storage.get_base_url()}/sell/inventory/v1/inventory_item?limit=1"
            response = requests.get(items_url, headers=headers, timeout=30)

            if response.status_code < 400:
                logger.info(
                    f"  ✅ Inventory Items API доступен: {response.status_code}"
                )

                # Проверяем количество товаров
                data = response.json()
                total_items = data.get("total", 0)
                logger.info(f"  Найдено инвентарных товаров: {total_items}")
            else:
                logger.warning(
                    f"  ❌ Ошибка доступа к Inventory Items API: {response.status_code}"
                )
                try:
                    error_data = response.json()
                    logger.warning(f"  Ответ: {json.dumps(error_data, indent=2)}")
                except:
                    logger.warning(f"  Ответ (не JSON): {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при проверке Inventory Items API: {e}")

        # 3. Проверка Inventory API - Offers
        try:
            logger.info("3. Проверка Inventory API (Offers):")
            offers_url = (
                f"{auth.token_storage.get_base_url()}/sell/inventory/v1/offer?limit=1"
            )
            response = requests.get(offers_url, headers=headers, timeout=30)

            if response.status_code < 400:
                logger.info(
                    f"  ✅ Inventory Offers API доступен: {response.status_code}"
                )

                # Проверяем количество предложений
                data = response.json()
                total_offers = data.get("total", 0)
                logger.info(f"  Найдено предложений: {total_offers}")
            else:
                logger.warning(
                    f"  ❌ Ошибка доступа к Inventory Offers API: {response.status_code}"
                )
                try:
                    error_data = response.json()
                    logger.warning(f"  Ответ: {json.dumps(error_data, indent=2)}")
                except:
                    logger.warning(f"  Ответ (не JSON): {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при проверке Inventory Offers API: {e}")

        # 4. Проверка Account API - Return Policies
        try:
            logger.info("4. Проверка Account API (Return Policies):")
            policies_url = f"{auth.token_storage.get_base_url()}/sell/account/v1/return_policy?marketplace_id=EBAY_DE"
            response = requests.get(policies_url, headers=headers, timeout=30)

            if response.status_code < 400:
                logger.info(
                    f"  ✅ Return Policies API доступен: {response.status_code}"
                )
            else:
                logger.warning(
                    f"  ❌ Ошибка доступа к Return Policies API: {response.status_code}"
                )
                try:
                    error_data = response.json()
                    logger.warning(f"  Ответ: {json.dumps(error_data, indent=2)}")
                except:
                    logger.warning(f"  Ответ (не JSON): {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при проверке Return Policies API: {e}")

        # 5. Проверка настроек продавца
        try:
            logger.info("5. Проверка настроек продавца (Seller API):")
            seller_url = (
                f"{auth.token_storage.get_base_url()}/sell/account/v1/privilege"
            )
            response = requests.get(seller_url, headers=headers, timeout=30)

            if response.status_code < 400:
                logger.info(
                    f"  ✅ Seller Privileges API доступен: {response.status_code}"
                )

                # Анализ привилегий
                data = response.json()
                logger.info(f"  Данные о привилегиях: {json.dumps(data, indent=2)}")
            else:
                logger.warning(
                    f"  ❌ Ошибка доступа к Seller Privileges API: {response.status_code}"
                )
                try:
                    error_data = response.json()
                    logger.warning(f"  Ответ: {json.dumps(error_data, indent=2)}")
                except:
                    logger.warning(f"  Ответ (не JSON): {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при проверке Seller Privileges API: {e}")

        # 6. Проверка типа аккаунта
        try:
            logger.info("6. Проверка типа аккаунта:")
            account_url = (
                f"{auth.token_storage.get_base_url()}/commerce/identity/v1/user"
            )
            response = requests.get(account_url, headers=headers, timeout=30)

            if response.status_code < 400:
                logger.info(f"  ✅ Identity API доступен: {response.status_code}")

                # Анализ данных аккаунта
                data = response.json()
                logger.info(f"  Данные об аккаунте: {json.dumps(data, indent=2)}")
            else:
                logger.warning(
                    f"  ❌ Ошибка доступа к Identity API: {response.status_code}"
                )
                try:
                    error_data = response.json()
                    logger.warning(f"  Ответ: {json.dumps(error_data, indent=2)}")
                except:
                    logger.warning(f"  Ответ (не JSON): {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при проверке Identity API: {e}")

        # 7. Проверка существующих местоположений с различными параметрами
        try:
            logger.info("7. Проверка существующих местоположений:")
            # Проверка с параметром limit
            location_url = f"{auth.token_storage.get_base_url()}/sell/inventory/v1/location?limit=5"
            response = requests.get(location_url, headers=headers, timeout=30)

            if response.status_code < 400:
                logger.info(f"  ✅ Location API доступен: {response.status_code}")

                # Анализ местоположений
                data = response.json()
                logger.info(f"  Данные о местоположениях: {json.dumps(data, indent=2)}")
            else:
                logger.warning(
                    f"  ❌ Ошибка доступа к Location API: {response.status_code}"
                )
                try:
                    error_data = response.json()
                    logger.warning(f"  Ответ: {json.dumps(error_data, indent=2)}")
                except:
                    logger.warning(f"  Ответ (не JSON): {response.text}")

            # Проверка с параметром merchant_location_status
            location_url = f"{auth.token_storage.get_base_url()}/sell/inventory/v1/location?merchant_location_status=ENABLED"
            response = requests.get(location_url, headers=headers, timeout=30)

            if response.status_code < 400:
                logger.info(
                    f"  ✅ Location API с фильтром статуса доступен: {response.status_code}"
                )

                # Анализ местоположений
                data = response.json()
                logger.info(f"  Данные о местоположениях: {json.dumps(data, indent=2)}")
            else:
                logger.warning(
                    f"  ❌ Ошибка доступа к Location API с фильтром статуса: {response.status_code}"
                )
                try:
                    error_data = response.json()
                    logger.warning(f"  Ответ: {json.dumps(error_data, indent=2)}")
                except:
                    logger.warning(f"  Ответ (не JSON): {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при проверке Location API: {e}")

    except Exception as e:
        logger.error(f"Общая ошибка при проверке API: {e}")

    # Итоговое заключение
    logger.info("\n=== ИТОГОВОЕ ЗАКЛЮЧЕНИЕ ===")
    logger.info(
        "1. Проверьте результаты вышеуказанных тестов для определения доступных API"
    )
    logger.info("2. Обратите внимание на ошибки доступа к Location API")
    logger.info(
        "3. Если ошибки 400 Bad Request повторяются для Location API, но другие API работают,"
    )
    logger.info(
        "   это может указывать на ограничения аккаунта или неполную активацию в Developer Portal"
    )

    return True


if __name__ == "__main__":
    check_account_privileges()
