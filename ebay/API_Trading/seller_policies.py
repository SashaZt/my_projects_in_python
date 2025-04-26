# seller_policies.py

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from xml.etree import ElementTree as ET

import requests
from ebay.API_Trading.ebay_auth.auth import EbayAuth
from logger import logger

from config import CLIENT_ID, CLIENT_SECRET, DEFAULT_MARKETPLACE_ID, RUNAME

# Trading API endpoint для Sandbox
API_ENDPOINT = "https://api.sandbox.ebay.com/ws/api.dll"


class EbaySellerPolicies:
    def __init__(self):
        self.auth = EbayAuth()
        self.token = self.auth.user_token

        if not self.token or not self.auth.token_storage.is_access_token_valid():
            logger.info("Токен истек или отсутствует. Пытаемся обновить.")
            token_data = self.auth.refresh_user_token()
            if token_data:
                self.token = token_data.get("access_token")
            else:
                raise Exception("Не удалось обновить токен.")

    def get_user_preferences(self):
        """Получение существующих профилей продавца через Trading API."""
        headers = {
            "Content-Type": "text/xml",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "X-EBAY-API-CALL-NAME": "GetUserPreferences",
            "X-EBAY-API-SITEID": "77",  # Germany
            "X-EBAY-API-IAF-TOKEN": self.token,
        }

        xml_request = f"""<?xml version="1.0" encoding="utf-8"?>
        <GetUserPreferencesRequest xmlns="urn:ebay:apis:eBLBaseComponents">
            <ShowSellerProfilePreferences>true</ShowSellerProfilePreferences>
        </GetUserPreferencesRequest>"""

        try:
            logger.info("Отправка запроса GetUserPreferences")
            response = requests.post(API_ENDPOINT, headers=headers, data=xml_request)
            logger.info(f"Ответ сервера GetUserPreferences: {response.text}")

            if response.status_code == 200:
                root = ET.fromstring(response.text)
                profiles = {}

                # Проверка наличия SellerProfilePreferences
                seller_profiles = root.find(".//SellerProfilePreferences")
                if seller_profiles is not None:
                    # Проверка статуса включения профилей
                    opted_in = seller_profiles.find("SellerProfileOptedIn")
                    if opted_in is not None and opted_in.text == "true":
                        # Извлечение профилей
                        supported_profiles = seller_profiles.findall(
                            ".//SupportedSellerProfile"
                        )

                        for profile in supported_profiles:
                            profile_id = profile.find("ProfileID")
                            profile_type = profile.find("ProfileType")
                            profile_name = profile.find("ProfileName")

                            if profile_id is not None and profile_type is not None:
                                profile_id_text = profile_id.text
                                profile_type_text = profile_type.text
                                profile_name_text = (
                                    profile_name.text
                                    if profile_name is not None
                                    else "Unnamed Profile"
                                )

                                if profile_type_text == "SHIPPING":
                                    profiles["SHIPPING_POLICY_ID"] = profile_id_text
                                    profiles["shipping_name"] = profile_name_text
                                elif profile_type_text == "RETURN_POLICY":
                                    profiles["RETURN_POLICY_ID"] = profile_id_text
                                    profiles["return_name"] = profile_name_text
                                elif profile_type_text == "PAYMENT":
                                    profiles["PAYMENT_POLICY_ID"] = profile_id_text
                                    profiles["payment_name"] = profile_name_text

                logger.info(f"Профили продавца: {profiles}")
                return profiles
            else:
                logger.error(
                    f"Ошибка GetUserPreferences: {response.status_code} - {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"Исключение при получении профилей продавца: {str(e)}")
            return None

    def get_seller_locations(self):
        """Получение местоположений продавца через Inventory API."""
        url = "https://api.sandbox.ebay.com/sell/inventory/v1/location"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            logger.info("Отправка запроса для получения местоположений продавца")
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Местоположения продавца: {data}")

                if "locations" in data and data["locations"]:
                    merchant_location_key = data["locations"][0]["merchantLocationKey"]
                    return {"MERCHANT_LOCATION_KEY": merchant_location_key}
                else:
                    logger.warning("Местоположения продавца не найдены")
                    return None
            else:
                logger.error(
                    f"Ошибка при получении местоположений: {response.status_code} - {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"Исключение при получении местоположений продавца: {str(e)}")
            return None

    def create_merchant_location(self, location_key="default-location"):
        """Создание местоположения продавца для инвентаря."""
        url = f"https://api.sandbox.ebay.com/sell/inventory/v1/location/{location_key}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        location_data = {
            "name": "Main Warehouse",
            "locationWebUrl": "http://example.com/warehouse",
            "phone": "+491234567890",
            "locationTypes": ["WAREHOUSE"],
            "merchantLocationStatus": "ENABLED",
            "locationInstructions": "Standard warehouse location",
            "address": {
                "addressLine1": "Musterstr. 1",
                "city": "Berlin",
                "stateOrProvince": "Berlin",
                "postalCode": "10115",
                "country": "DE",
            },
        }

        try:
            logger.info(f"Создание местоположения продавца с ключом {location_key}")
            response = requests.post(url, headers=headers, json=location_data)

            if response.status_code == 204:  # Успешное создание без содержимого
                logger.info(f"Местоположение {location_key} успешно создано")
                return {"MERCHANT_LOCATION_KEY": location_key}
            else:
                logger.error(
                    f"Ошибка при создании местоположения: {response.status_code} - {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"Исключение при создании местоположения продавца: {str(e)}")
            return None

    def get_payment_policies(self):
        """Получение платежных политик."""
        url = "https://api.sandbox.ebay.com/sell/account/v1/payment_policy"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        params = {"marketplace_id": DEFAULT_MARKETPLACE_ID}

        try:
            logger.info("Отправка запроса для получения платежных политик")
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Платежные политики: {data}")

                if "paymentPolicies" in data and data["paymentPolicies"]:
                    policy = data["paymentPolicies"][0]
                    policy_id = policy["paymentPolicyId"]
                    policy_name = policy["name"]
                    return {"PAYMENT_POLICY_ID": policy_id, "payment_name": policy_name}
                else:
                    logger.warning("Платежные политики не найдены")
                    return None
            else:
                logger.error(
                    f"Ошибка при получении платежных политик: {response.status_code} - {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"Исключение при получении платежных политик: {str(e)}")
            return None

    def get_return_policies(self):
        """Получение политик возврата."""
        url = "https://api.sandbox.ebay.com/sell/account/v1/return_policy"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        params = {"marketplace_id": DEFAULT_MARKETPLACE_ID}

        try:
            logger.info("Отправка запроса для получения политик возврата")
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Политики возврата: {data}")

                if "returnPolicies" in data and data["returnPolicies"]:
                    policy = data["returnPolicies"][0]
                    policy_id = policy["returnPolicyId"]
                    policy_name = policy["name"]
                    return {"RETURN_POLICY_ID": policy_id, "return_name": policy_name}
                else:
                    logger.warning("Политики возврата не найдены")
                    return None
            else:
                logger.error(
                    f"Ошибка при получении политик возврата: {response.status_code} - {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"Исключение при получении политик возврата: {str(e)}")
            return None

    def get_fulfillment_policies(self):
        """Получение политик доставки."""
        url = "https://api.sandbox.ebay.com/sell/account/v1/fulfillment_policy"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        params = {"marketplace_id": DEFAULT_MARKETPLACE_ID}

        try:
            logger.info("Отправка запроса для получения политик доставки")
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Политики доставки: {data}")

                if "fulfillmentPolicies" in data and data["fulfillmentPolicies"]:
                    policy = data["fulfillmentPolicies"][0]
                    policy_id = policy["fulfillmentPolicyId"]
                    policy_name = policy["name"]
                    return {
                        "SHIPPING_POLICY_ID": policy_id,
                        "shipping_name": policy_name,
                    }
                else:
                    logger.warning("Политики доставки не найдены")
                    return None
            else:
                logger.error(
                    f"Ошибка при получении политик доставки: {response.status_code} - {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"Исключение при получении политик доставки: {str(e)}")
            return None

    def create_payment_policy(self, policy_data=None):
        """Создание платежной политики."""
        if policy_data is None:
            policy_data = {
                "name": "Standard Payment Policy DE",
                "description": "Standard payment policy for eBay Germany",
                "marketplaceId": DEFAULT_MARKETPLACE_ID,
                "categoryTypes": [
                    {"name": "ALL_EXCLUDING_MOTORS_VEHICLES", "default": True}
                ],
                "paymentMethods": [
                    {
                        "paymentMethodType": "PAYPAL",
                        "recipientAccountReference": {
                            "referenceType": "PAYPAL_EMAIL",
                            "referenceId": "test-paypal@example.com",
                        },
                    }
                ],
            }

        url = "https://api.sandbox.ebay.com/sell/account/v1/payment_policy"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            logger.info("Создание платежной политики")
            response = requests.post(url, headers=headers, json=policy_data)

            if response.status_code == 201:
                data = response.json()
                logger.info(f"Платежная политика создана: {data}")
                policy_id = data.get("paymentPolicyId")
                policy_name = data.get("name")
                return {"PAYMENT_POLICY_ID": policy_id, "payment_name": policy_name}
            else:
                logger.error(
                    f"Ошибка при создании платежной политики: {response.status_code} - {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"Исключение при создании платежной политики: {str(e)}")
            return None

    def create_return_policy(self, policy_data=None):
        """Создание политики возврата."""
        if policy_data is None:
            policy_data = {
                "name": "Standard Return Policy DE",
                "description": "Standard 30-day return policy for Germany",
                "marketplaceId": DEFAULT_MARKETPLACE_ID,
                "categoryTypes": [
                    {"name": "ALL_EXCLUDING_MOTORS_VEHICLES", "default": True}
                ],
                "returnsAccepted": True,
                "returnPeriod": {"value": 30, "unit": "DAY"},
                "refundMethod": "MONEY_BACK",
                "returnShippingCostPayer": "SELLER",
                "returnMethod": "REPLACEMENT",
            }

        url = "https://api.sandbox.ebay.com/sell/account/v1/return_policy"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            logger.info("Создание политики возврата")
            response = requests.post(url, headers=headers, json=policy_data)

            if response.status_code == 201:
                data = response.json()
                logger.info(f"Политика возврата создана: {data}")
                policy_id = data.get("returnPolicyId")
                policy_name = data.get("name")
                return {"RETURN_POLICY_ID": policy_id, "return_name": policy_name}
            else:
                logger.error(
                    f"Ошибка при создании политики возврата: {response.status_code} - {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"Исключение при создании политики возврата: {str(e)}")
            return None

    def create_fulfillment_policy(self, policy_data=None):
        """Создание политики доставки."""
        if policy_data is None:
            policy_data = {
                "name": "Standard Shipping Policy DE",
                "description": "Standard shipping policy for Germany",
                "marketplaceId": DEFAULT_MARKETPLACE_ID,
                "categoryTypes": [
                    {"name": "ALL_EXCLUDING_MOTORS_VEHICLES", "default": True}
                ],
                "handlingTime": {"value": 1, "unit": "DAY"},
                "shippingOptions": [
                    {
                        "optionType": "DOMESTIC",
                        "costType": "FLAT_RATE",
                        "shippingServices": [
                            {
                                "sortOrder": 1,
                                "shippingCarrierCode": "DHL",
                                "shippingServiceCode": "DE_DHLPaket",
                                "shippingCost": {"currency": "EUR", "value": "5.99"},
                                "additionalShippingCost": {
                                    "currency": "EUR",
                                    "value": "1.99",
                                },
                            }
                        ],
                    }
                ],
            }

        url = "https://api.sandbox.ebay.com/sell/account/v1/fulfillment_policy"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            logger.info("Создание политики доставки")
            response = requests.post(url, headers=headers, json=policy_data)

            if response.status_code == 201:
                data = response.json()
                logger.info(f"Политика доставки создана: {data}")
                policy_id = data.get("fulfillmentPolicyId")
                policy_name = data.get("name")
                return {"SHIPPING_POLICY_ID": policy_id, "shipping_name": policy_name}
            else:
                logger.error(
                    f"Ошибка при создании политики доставки: {response.status_code} - {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"Исключение при создании политики доставки: {str(e)}")
            return None


def get_seller_profiles():
    """Получение всех существующих профилей продавца."""
    try:
        policies = EbaySellerPolicies()

        # Получение профилей из Trading API
        trading_profiles = policies.get_user_preferences() or {}

        # Получение профилей из Account API
        payment_profiles = policies.get_payment_policies() or {}
        return_profiles = policies.get_return_policies() or {}
        fulfillment_profiles = policies.get_fulfillment_policies() or {}

        # Получение местоположений из Inventory API
        location_profiles = policies.get_seller_locations() or {}

        # Объединение всех профилей
        all_profiles = {
            **trading_profiles,
            **payment_profiles,
            **return_profiles,
            **fulfillment_profiles,
            **location_profiles,
        }

        # Сохранение профилей в файл
        save_policy_ids(all_profiles)

        return all_profiles
    except Exception as e:
        logger.error(f"Ошибка при получении профилей продавца: {str(e)}")
        return None


def setup_seller_profiles(load_from_json=True):
    """Настройка профилей продавца."""
    try:
        policies = EbaySellerPolicies()
        config_updates = {}

        # Шаг 1: Проверка наличия существующих профилей
        existing_profiles = get_seller_profiles()
        if existing_profiles:
            logger.info("Найдены существующие профили продавца")
            return existing_profiles

        # Шаг 2: Если профили не найдены, создаём новые
        logger.info("Существующие профили не найдены. Создание новых профилей...")

        # Создание местоположения
        location_result = policies.create_merchant_location("default-location")
        if location_result:
            config_updates.update(location_result)

        # Создание платежной политики
        payment_data = None
        if load_from_json:
            try:
                with open("policy/payment_policy.json", "r", encoding="utf-8") as f:
                    payment_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.warning(f"Не удалось загрузить payment_policy.json: {e}")

        payment_result = policies.create_payment_policy(payment_data)
        if payment_result:
            config_updates.update(payment_result)

        # Создание политики возврата
        return_data = None
        if load_from_json:
            try:
                with open("policy/return_policy.json", "r", encoding="utf-8") as f:
                    return_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.warning(f"Не удалось загрузить return_policy.json: {e}")

        return_result = policies.create_return_policy(return_data)
        if return_result:
            config_updates.update(return_result)

        # Создание политики доставки
        fulfillment_data = None
        if load_from_json:
            try:
                with open("policy/fulfillment_policy.json", "r", encoding="utf-8") as f:
                    fulfillment_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.warning(f"Не удалось загрузить fulfillment_policy.json: {e}")

        fulfillment_result = policies.create_fulfillment_policy(fulfillment_data)
        if fulfillment_result:
            config_updates.update(fulfillment_result)

        # Сохранение профилей в файл
        if config_updates:
            save_policy_ids(config_updates)

        return config_updates
    except Exception as e:
        logger.error(f"Ошибка при настройке профилей продавца: {str(e)}")
        return None


def save_policy_ids(config_updates):
    """Сохранение ID политик в файл policy_ids.json."""
    try:
        # Путь к файлу конфигурации
        config_file = Path("config/policy_ids.json")
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Чтение существующей конфигурации, если файл существует
        existing_config = {}
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    existing_config = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Ошибка чтения {config_file}. Файл будет перезаписан.")

        # Обновление конфигурации
        existing_config.update(config_updates)

        # Сохранение обновленной конфигурации
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(existing_config, f, indent=4, ensure_ascii=False)

        logger.info(f"ID политик сохранены в файл {config_file}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении ID политик: {e}")
        return False


def main():
    """Основная функция для настройки профилей продавца."""
    logger.info("Запуск скрипта настройки политик продавца...")

    # Проверка наличия существующих политик
    logger.info("Проверка наличия существующих политик продавца...")
    existing_profiles = get_seller_profiles()

    if existing_profiles:
        logger.info("Существующие политики найдены и сохранены:")
        for key, value in existing_profiles.items():
            if key.endswith("_ID"):
                logger.info(f"  {key}: {value}")
    else:
        logger.info("Существующие политики не найдены. Создание новых политик...")
        new_profiles = setup_seller_profiles()

        if new_profiles:
            logger.info("Политики продавца успешно созданы и сохранены:")
            for key, value in new_profiles.items():
                if key.endswith("_ID"):
                    logger.info(f"  {key}: {value}")
        else:
            logger.error("Не удалось создать политики продавца.")

    logger.info("Выполнение скрипта завершено.")


if __name__ == "__main__":
    main()
