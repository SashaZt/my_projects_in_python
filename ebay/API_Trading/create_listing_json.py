import csv
import json
import time
import urllib.parse
import webbrowser
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

import requests
from ebay_auth_manager import EbayAuthManager
from logger import logger
from token_storage import TokenStorage

from config import (
    AUTH_URL,
    CLIENT_ID,
    CLIENT_SECRET,
    DEFAULT_MARKETPLACE_ID,
    RUNAME,
    TOKEN_URL,
    USER_SCOPES,
)

# Trading API endpoint для Sandbox
API_ENDPOINT = "https://api.sandbox.ebay.com/ws/api.dll"
# OAuth авторизационная страница для Sandbox
AUTH_URL = "https://auth.sandbox.ebay.com/oauth2/authorize"


class EbayTradingAPI:
    def __init__(self):
        self.auth = EbayAuthManager()
        self.token = self.auth.authenticate()

        if not self.token:
            raise Exception("Не удалось получить токен аутентификации.")

    def get_shipping_services(self):
        """Получение списка поддерживаемых служб доставки."""
        headers = {
            "Content-Type": "text/xml",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "X-EBAY-API-CALL-NAME": "GeteBayDetails",
            "X-EBAY-API-SITEID": "77",
            "X-EBAY-API-IAF-TOKEN": self.token,
        }
        xml_request = f"""<?xml version="1.0" encoding="utf-8"?>
        <GeteBayDetailsRequest xmlns="urn:ebay:apis:eBLBaseComponents">
            <DetailName>ShippingServiceDetails</DetailName>
        </GeteBayDetailsRequest>"""
        try:
            logger.info("Отправка запроса GeteBayDetails")
            response = requests.post(API_ENDPOINT, headers=headers, data=xml_request)
            logger.info(f"Ответ сервера GeteBayDetails: {response.text}")
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                services = root.findall(".//ShippingServiceDetails")
                shipping_services = [
                    s.find("ShippingService").text
                    for s in services
                    if s.find("ShippingService") is not None
                ]
                logger.info(f"Поддерживаемые службы доставки: {shipping_services}")
                return shipping_services
            else:
                logger.error(
                    f"Ошибка GeteBayDetails: {response.status_code} - {response.text}"
                )
                raise Exception(f"Ошибка GeteBayDetails: {response.text}")
        except Exception as e:
            logger.error(f"Исключение при получении служб доставки: {str(e)}")
            raise

    def get_seller_profiles(self):
        """Получение ID профилей продавца."""
        headers = {
            "Content-Type": "text/xml",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "X-EBAY-API-CALL-NAME": "GetUserPreferences",
            "X-EBAY-API-SITEID": "77",
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
                namespaces = {"ns": "urn:ebay:apis:eBLBaseComponents"}
                supported_profiles = root.findall(
                    ".//ns:SupportedSellerProfile", namespaces
                )
                for profile in supported_profiles:
                    profile_id_elem = profile.find("ns:ProfileID", namespaces)
                    profile_type_elem = profile.find("ns:ProfileType", namespaces)
                    profile_name_elem = profile.find("ns:ProfileName", namespaces)
                    if profile_id_elem is not None and profile_type_elem is not None:
                        profile_id = profile_id_elem.text
                        profile_type = profile_type_elem.text
                        profile_name = (
                            profile_name_elem.text
                            if profile_name_elem is not None
                            else ""
                        )
                        if profile_type == "SHIPPING":
                            profiles["shipping_id"] = profile_id
                            profiles["shipping_name"] = profile_name
                        elif profile_type == "RETURN_POLICY":
                            profiles["return_id"] = profile_id
                            profiles["return_name"] = profile_name
                        elif profile_type == "PAYMENT":
                            profiles["payment_id"] = profile_id
                            profiles["payment_name"] = profile_name
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

    def verify_add_fixed_price_item(self, item_data=None):
        """Проверка листинга с помощью VerifyAddFixedPriceItem."""
        headers = {
            "Content-Type": "text/xml",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "X-EBAY-API-CALL-NAME": "VerifyAddFixedPriceItem",
            "X-EBAY-API-SITEID": "77",
            "X-EBAY-API-IAF-TOKEN": self.token,
        }
        xml_request = self._build_fixed_price_item_xml(
            item_data, request_type="VerifyAddFixedPriceItem"
        )
        try:
            logger.info("Отправка запроса VerifyAddFixedPriceItem")
            response = requests.post(API_ENDPOINT, headers=headers, data=xml_request)
            logger.info(f"Ответ сервера VerifyAddFixedPriceItem: {response.text}")
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                namespaces = {"ns": "urn:ebay:apis:eBLBaseComponents"}
                ack = root.find(".//ns:Ack", namespaces)
                if ack is None:
                    logger.error(f"Элемент Ack не найден в ответе: {response.text}")
                    raise Exception(
                        f"Неверный формат ответа VerifyAddFixedPriceItem: {response.text}"
                    )
                if ack.text == "Success":
                    logger.info("Листинг прошел проверку VerifyAddFixedPriceItem")
                    return True
                else:
                    errors = root.findall(".//ns:Errors", namespaces)
                    error_messages = []
                    for e in errors:
                        long_msg = e.find(".//ns:LongMessage", namespaces)
                        short_msg = e.find(".//ns:ShortMessage", namespaces)
                        msg = (
                            long_msg.text
                            if long_msg is not None
                            else (
                                short_msg.text
                                if short_msg is not None
                                else "Неизвестная ошибка"
                            )
                        )
                        error_messages.append(msg)
                    logger.error(f"Ошибка проверки листинга: {error_messages}")
                    raise Exception(f"Ошибка VerifyAddFixedPriceItem: {error_messages}")
            else:
                logger.error(
                    f"Ошибка VerifyAddFixedPriceItem: {response.status_code} - {response.text}"
                )
                raise Exception(f"Ошибка VerifyAddFixedPriceItem: {response.text}")
        except Exception as e:
            logger.error(f"Исключение при проверке листинга: {str(e)}")
            raise

    def add_fixed_price_item(self, item_data=None):
        """Создание листинга с помощью AddFixedPriceItem."""
        headers = {
            "Content-Type": "text/xml",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "X-EBAY-API-CALL-NAME": "AddFixedPriceItem",
            "X-EBAY-API-SITEID": "77",
            "X-EBAY-API-IAF-TOKEN": self.token,
        }
        xml_request = self._build_fixed_price_item_xml(
            item_data, request_type="AddFixedPriceItem"
        )
        try:
            logger.info("Отправка запроса AddFixedPriceItem")
            response = requests.post(API_ENDPOINT, headers=headers, data=xml_request)
            logger.info(f"Ответ сервера AddFixedPriceItem: {response.text}")
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                namespaces = {"ns": "urn:ebay:apis:eBLBaseComponents"}
                ack = root.find(".//ns:Ack", namespaces)
                if ack is None:
                    logger.error(f"Элемент Ack не найден в ответе: {response.text}")
                    raise Exception(
                        f"Неверный формат ответа AddFixedPriceItem: {response.text}"
                    )
                if ack.text in ["Success", "Warning"]:
                    item_id = root.find(".//ns:ItemID", namespaces)
                    item_id_text = item_id.text if item_id is not None else "Unknown"
                    logger.info(f"Листинг успешно создан, ItemID: {item_id_text}")
                    return item_id_text
                else:
                    errors = root.findall(".//ns:Errors", namespaces)
                    error_messages = []
                    for e in errors:
                        long_msg = e.find(".//ns:LongMessage", namespaces)
                        short_msg = e.find(".//ns:ShortMessage", namespaces)
                        msg = (
                            long_msg.text
                            if long_msg is not None
                            else (
                                short_msg.text
                                if short_msg is not None
                                else "Неизвестная ошибка"
                            )
                        )
                        error_messages.append(msg)
                    logger.error(f"Ошибка при создании листинга: {error_messages}")
                    raise Exception(f"Ошибка AddFixedPriceItem: {error_messages}")
            else:
                logger.error(
                    f"Ошибка AddFixedPriceItem: {response.status_code} - {response.text}"
                )
                raise Exception(f"Ошибка AddFixedPriceItem: {response.text}")
        except Exception as e:
            logger.error(f"Исключение при создании листинга: {str(e)}")
            raise

    def revise_fixed_price_item(self, item_id, item_data=None):
        """Обновление листинга с помощью ReviseFixedPriceItem."""
        headers = {
            "Content-Type": "text/xml",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "X-EBAY-API-CALL-NAME": "ReviseFixedPriceItem",
            "X-EBAY-API-SITEID": "77",
            "X-EBAY-API-IAF-TOKEN": self.token,
        }
        xml_request = self._build_fixed_price_item_xml(
            item_data, request_type="ReviseFixedPriceItem", item_id=item_id
        )
        try:
            logger.info(f"Отправка запроса ReviseFixedPriceItem для ItemID: {item_id}")
            logger.debug(f"XML запрос ReviseFixedPriceItem: {xml_request}")
            response = requests.post(API_ENDPOINT, headers=headers, data=xml_request)
            logger.info(f"Ответ сервера ReviseFixedPriceItem: {response.text}")
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                namespaces = {"ns": "urn:ebay:apis:eBLBaseComponents"}
                ack = root.find(".//ns:Ack", namespaces)
                if ack is None:
                    logger.error(f"Элемент Ack не найден в ответе: {response.text}")
                    raise Exception(
                        f"Неверный формат ответа ReviseFixedPriceItem: {response.text}"
                    )
                if ack.text in ["Success", "Warning"]:
                    item_id_elem = root.find(".//ns:ItemID", namespaces)
                    item_id_text = (
                        item_id_elem.text if item_id_elem is not None else item_id
                    )
                    logger.info(f"Листинг успешно обновлен, ItemID: {item_id_text}")
                    return item_id_text
                else:
                    errors = root.findall(".//ns:Errors", namespaces)
                    error_messages = []
                    for e in errors:
                        long_msg = e.find(".//ns:LongMessage", namespaces)
                        short_msg = e.find(".//ns:ShortMessage", namespaces)
                        msg = (
                            long_msg.text
                            if long_msg is not None
                            else (
                                short_msg.text
                                if short_msg is not None
                                else "Неизвестная ошибка"
                            )
                        )
                        error_messages.append(msg)
                    logger.error(f"Ошибка при обновлении листинга: {error_messages}")
                    raise Exception(f"Ошибка ReviseFixedPriceItem: {error_messages}")
            else:
                logger.error(
                    f"Ошибка ReviseFixedPriceItem: {response.status_code} - {response.text}"
                )
                raise Exception(f"Ошибка ReviseFixedPriceItem: {response.text}")
        except Exception as e:
            logger.error(f"Исключение при обновлении листинга: {str(e)}")
            raise

    def _build_fixed_price_item_xml(
        self, item_data=None, request_type="AddFixedPriceItem", item_id=None
    ):
        """Формирование XML для AddFixedPriceItem, VerifyAddFixedPriceItem или ReviseFixedPriceItem."""
        item_data = item_data or {}
        title = item_data.get("Title", "Designer Women's Handbag - Black Leather")
        description = item_data.get(
            "Description",
            "Elegant black leather handbag, perfect for daily use. Brand new, high quality.",
        )
        price = item_data.get("Price", "50.00")
        quantity = item_data.get("Quantity", "1")
        category_id = item_data.get("CategoryID", "169291")
        condition_id = item_data.get("ConditionID", "1000")
        color = item_data.get("Color", "Schwarz")
        material = item_data.get("Material", "Echtleder")
        style = item_data.get("Style", "Schultertasche")
        brand = item_data.get("Brand", "Handmade")
        department = item_data.get("Department", "Damen")
        image_url = item_data.get("ImageURL", "https://example.com/handbag.jpg")
        sku = item_data.get("SKU", "")
        ean = item_data.get("EAN", "Nicht zutreffend")
        postal_code = item_data.get("PostalCode", "10115")
        dispatch_time_max = item_data.get("DispatchTimeMax", "3")
        profiles = self.get_seller_profiles() or {}
        shipping_profile_id = profiles.get("shipping_id", "6208596000")
        return_profile_id = profiles.get("return_id", "6208750000")
        payment_profile_id = profiles.get("payment_id", "6208882000")

        # Определяем корневой тег в зависимости от request_type
        root_tag = {
            "VerifyAddFixedPriceItem": "VerifyAddFixedPriceItemRequest",
            "AddFixedPriceItem": "AddFixedPriceItemRequest",
            "ReviseFixedPriceItem": "ReviseFixedPriceItemRequest",
        }.get(request_type, "AddFixedPriceItemRequest")

        xml = f"""<?xml version="1.0" encoding="utf-8"?>
        <{root_tag} xmlns="urn:ebay:apis:eBLBaseComponents">
            <Item>
        """
        if request_type == "ReviseFixedPriceItem" and item_id:
            xml += f"        <ItemID>{item_id}</ItemID>\n"
        xml += f"""        <Title>{title}</Title>
                <Description>{description}</Description>
                <PrimaryCategory>
                    <CategoryID>{category_id}</CategoryID>
                </PrimaryCategory>
                <StartPrice currencyID="EUR">{price}</StartPrice>
                <ConditionID>{condition_id}</ConditionID>
                <Country>DE</Country>
                <Currency>EUR</Currency>
                <DispatchTimeMax>{dispatch_time_max}</DispatchTimeMax>
                <ListingDuration>GTC</ListingDuration>
                <ListingType>FixedPriceItem</ListingType>
                <ItemSpecifics>
                    <NameValueList>
                        <Name>Stil</Name>
                        <Value>{style}</Value>
                    </NameValueList>
                    <NameValueList>
                        <Name>Außenmaterial</Name>
                        <Value>{material}</Value>
                    </NameValueList>
                    <NameValueList>
                        <Name>Außenfarbe</Name>
                        <Value>{color}</Value>
                    </NameValueList>
                    <NameValueList>
                        <Name>Marke</Name>
                        <Value>{brand}</Value>
                    </NameValueList>
                    <NameValueList>
                        <Name>Abteilung</Name>
                        <Value>{department}</Value>
                    </NameValueList>
                </ItemSpecifics>
                <ProductListingDetails>
                    <EAN>{ean}</EAN>
                </ProductListingDetails>
                <SellerProfiles>
                    <SellerShippingProfile>
                        <ShippingProfileID>{shipping_profile_id}</ShippingProfileID>
                    </SellerShippingProfile>
                    <SellerReturnProfile>
                        <ReturnProfileID>{return_profile_id}</ReturnProfileID>
                    </SellerReturnProfile>
                    <SellerPaymentProfile>
                        <PaymentProfileID>{payment_profile_id}</PaymentProfileID>
                    </SellerPaymentProfile>
                </SellerProfiles>
                <PictureDetails>
                    <PictureURL>{image_url}</PictureURL>
                </PictureDetails>
                <PostalCode>{postal_code}</PostalCode>
                <Quantity>{quantity}</Quantity>
                <Site>Germany</Site>
        """
        if sku:
            xml += f"        <SKU>{sku}</SKU>\n"
        xml += f"""    </Item>
        </{root_tag}>"""
        return xml

    def get_category_specifics(self, category_id):
        """Получение обязательных и рекомендуемых ItemSpecifics для категории."""
        # Проверка токена
        if not self.token:
            logger.error("Токен отсутствует или недействителен")
            raise ValueError("Токен отсутствует")

        # Формируем заголовки без IAF токена
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "X-EBAY-API-CALL-NAME": "GetCategorySpecifics",
            "X-EBAY-API-SITEID": "77",  # Германия
        }

        # В XML включаем токен, как показано в примере документации
        xml_request = f"""<?xml version="1.0" encoding="utf-8"?>
        <GetCategorySpecificsRequest xmlns="urn:ebay:apis:eBLBaseComponents">
            <RequesterCredentials>
                <eBayAuthToken>{self.token}</eBayAuthToken>
            </RequesterCredentials>
            <CategorySpecific>
                <CategoryID>{category_id}</CategoryID>
            </CategorySpecific>
        </GetCategorySpecificsRequest>"""

        max_retries = 5
        retry_delay = 5
        timeout = 60

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Отправка запроса GetCategorySpecifics для CategoryID: {category_id}, попытка {attempt + 1}/{max_retries}"
                )
                # Безопасное логирование запроса (скрываем токен)
                safe_xml = xml_request.replace(self.token, "TOKEN_HIDDEN")
                logger.debug(f"Заголовки запроса: {headers}")
                logger.debug(f"XML запрос: {safe_xml}")

                # Отправка запроса
                response = requests.post(
                    API_ENDPOINT, headers=headers, data=xml_request, timeout=timeout
                )

                # Проверяем код ответа
                response.raise_for_status()

                # Логируем ответ сервера
                logger.info(
                    f"Получен ответ сервера GetCategorySpecifics (статус {response.status_code})"
                )

                # Проверка кода ответа и обработка XML
                if response.status_code == 200:
                    root = ET.fromstring(response.text)

                    # Проверка на наличие Errors в ответе
                    errors = root.findall(".//Errors")
                    if errors:
                        error_messages = []
                        for error in errors:
                            error_code = error.find("ErrorCode")
                            error_message = error.find("ShortMessage")
                            if error_code is not None and error_message is not None:
                                error_messages.append(
                                    f"Код ошибки: {error_code.text}, Сообщение: {error_message.text}"
                                )

                        error_text = "; ".join(error_messages)
                        logger.error(f"Ошибка в ответе API: {error_text}")

                        # Проверка на конкретные ошибки
                        if any(
                            "token" in msg.lower() or "auth" in msg.lower()
                            for msg in error_messages
                        ):
                            logger.error(
                                "Ошибка авторизации. Необходимо обновить токен."
                            )
                            return None

                        if attempt < max_retries - 1:
                            delay = retry_delay * (attempt + 1)
                            logger.info(f"Повторная попытка через {delay} секунд...")
                            time.sleep(delay)
                            continue

                    # Проверка успешного ответа
                    ack = root.find(".//Ack")
                    if (
                        ack is not None
                        and ack.text != "Success"
                        and ack.text != "Warning"
                    ):
                        logger.error(f"Неуспешный ответ API: {ack.text}")
                        if attempt < max_retries - 1:
                            delay = retry_delay * (attempt + 1)
                            logger.info(f"Повторная попытка через {delay} секунд...")
                            time.sleep(delay)
                            continue
                        return None

                    # Парсинг данных с правильными namespace
                    namespaces = {"ns": "urn:ebay:apis:eBLBaseComponents"}
                    recommendations = root.findall(
                        ".//ns:NameRecommendation", namespaces
                    )

                    if not recommendations:
                        # Попробуем без namespace
                        recommendations = root.findall(".//NameRecommendation")

                    if not recommendations:
                        logger.warning(
                            f"В ответе не найдены рекомендации для категории {category_id}"
                        )
                        # Логирование части ответа для отладки
                        logger.debug(f"Часть ответа: {response.text[:500]}...")
                        return []

                    specifics = []
                    for rec in recommendations:
                        try:
                            # Поиск Name элемента
                            name_elem = rec.find("ns:Name", namespaces) or rec.find(
                                "Name"
                            )
                            if name_elem is None:
                                continue

                            name = name_elem.text

                            # Поиск правил валидации
                            validation = rec.find(
                                "ns:ValidationRules", namespaces
                            ) or rec.find("ValidationRules")

                            # Определение MinValues
                            min_values = 0
                            if validation is not None:
                                min_values_elem = validation.find(
                                    "ns:MinValues", namespaces
                                ) or validation.find("MinValues")
                                if (
                                    min_values_elem is not None
                                    and min_values_elem.text is not None
                                ):
                                    try:
                                        min_values = int(min_values_elem.text)
                                    except ValueError:
                                        pass

                            # Определение SelectionMode
                            selection_mode = "FreeText"
                            if validation is not None:
                                selection_mode_elem = validation.find(
                                    "ns:SelectionMode", namespaces
                                ) or validation.find("SelectionMode")
                                if (
                                    selection_mode_elem is not None
                                    and selection_mode_elem.text is not None
                                ):
                                    selection_mode = selection_mode_elem.text

                            # Поиск рекомендованных значений
                            values = []
                            value_recs = rec.findall(
                                ".//ns:ValueRecommendation/ns:Value", namespaces
                            ) or rec.findall(".//ValueRecommendation/Value")
                            for v in value_recs:
                                if v.text is not None:
                                    values.append(v.text)

                            specifics.append(
                                {
                                    "Name": name,
                                    "Required": min_values > 0,
                                    "SelectionMode": selection_mode,
                                    "Values": values,
                                }
                            )
                        except Exception as e:
                            logger.error(f"Ошибка при обработке рекомендации: {str(e)}")
                            continue

                    logger.info(
                        f"Получены ItemSpecifics для CategoryID {category_id}: {len(specifics)} специфик"
                    )
                    return specifics

                else:
                    logger.error(f"Неожиданный код ответа: {response.status_code}")
                    if attempt < max_retries - 1:
                        delay = retry_delay * (attempt + 1)
                        logger.info(f"Повторная попытка через {delay} секунд...")
                        time.sleep(delay)
                        continue
                    return None

            except requests.exceptions.ConnectionError as e:
                logger.error(
                    f"Ошибка соединения при получении ItemSpecifics (попытка {attempt + 1}/{max_retries}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    delay = retry_delay * (attempt + 1)
                    logger.info(f"Повторная попытка через {delay} секунд...")
                    time.sleep(delay)
                    continue
                logger.error("Все попытки соединения исчерпаны")
                return None

            except requests.exceptions.Timeout as e:
                logger.error(
                    f"Тайм-аут при получении ItemSpecifics (попытка {attempt + 1}/{max_retries}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    delay = retry_delay * (attempt + 1)
                    logger.info(f"Повторная попытка через {delay} секунд...")
                    time.sleep(delay)
                    continue
                return None

            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP ошибка при получении ItemSpecifics: {str(e)}")
                if hasattr(e, "response") and e.response is not None:
                    logger.error(f"Ответ сервера: {e.response.text}")
                if attempt < max_retries - 1:
                    delay = retry_delay * (attempt + 1)
                    logger.info(f"Повторная попытка через {delay} секунд...")
                    time.sleep(delay)
                    continue
                return None

            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка запроса GetCategorySpecifics: {str(e)}")
                if hasattr(e, "response") and e.response is not None:
                    logger.error(f"Ответ сервера: {e.response.text}")
                if attempt < max_retries - 1:
                    delay = retry_delay * (attempt + 1)
                    logger.info(f"Повторная попытка через {delay} секунд...")
                    time.sleep(delay)
                    continue
                return None

            except ET.ParseError as e:
                logger.error(f"Ошибка парсинга XML ответа: {str(e)}")
                logger.error(f"Полученный ответ: {response.text[:1000]}...")
                if attempt < max_retries - 1:
                    delay = retry_delay * (attempt + 1)
                    logger.info(f"Повторная попытка через {delay} секунд...")
                    time.sleep(delay)
                    continue
                return None

            except Exception as e:
                logger.error(
                    f"Необработанное исключение при получении ItemSpecifics: {str(e)}"
                )
                if attempt < max_retries - 1:
                    delay = retry_delay * (attempt + 1)
                    logger.info(f"Повторная попытка через {delay} секунд...")
                    time.sleep(delay)
                    continue
                return None


def load_items_from_json(file_path):
    """Чтение данных товаров из JSON."""
    try:
        with open(file_path, "r", encoding="utf-8") as jsonfile:
            items = json.load(jsonfile)
        logger.info(f"Загружено {len(items)} товаров из {file_path}")
        return items
    except Exception as e:
        logger.error(f"Ошибка при чтении JSON: {str(e)}")
        raise


def save_item_ids_to_json(items, item_ids, output_file="output_items.json"):
    """Сохранение товаров с ItemID в JSON."""
    try:
        updated_items = items.copy()  # Создаем копию, чтобы не изменять оригинал
        for item, item_id in zip(updated_items, item_ids):
            item["ItemID"] = item_id
        with open(output_file, "w", encoding="utf-8") as jsonfile:
            json.dump(updated_items, jsonfile, indent=4, ensure_ascii=False)
        logger.info(f"Товары с ItemID сохранены в {output_file}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении JSON: {str(e)}")
        raise


def update_items_from_json(trading_api, json_file="output_items.json"):
    """Обновление листингов из JSON-файла."""
    try:
        items = load_items_from_json(json_file)
        updated_item_ids = []
        for item in items:
            item_id = item.get("ItemID")
            if not item_id:
                logger.warning(
                    f"Пропущен товар без ItemID: {item.get('Title', 'Unknown')}"
                )
                continue
            try:
                updated_item_id = trading_api.revise_fixed_price_item(
                    item_id, item_data=item
                )
                logger.info(f"Листинг обновлен, ItemID: {updated_item_id}")
                print(f"Листинг обновлен, ItemID: {updated_item_id}")
                updated_item_ids.append(updated_item_id)
            except Exception as e:
                logger.error(f"Ошибка при обновлении листинга {item_id}: {str(e)}")
                print(f"Ошибка при обновлении листинга {item_id}: {str(e)}")
        logger.info(f"Обновлено {len(updated_item_ids)} листингов из {json_file}")
        return updated_item_ids
    except Exception as e:
        logger.error(f"Ошибка при обновлении листингов из JSON: {str(e)}")
        raise


def save_item_ids_to_csv(items, item_ids, output_file="output_items.csv"):
    """Сохранение ItemID в новый CSV."""
    try:
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = list(items[0].keys()) + ["ItemID"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item, item_id in zip(items, item_ids):
                item["ItemID"] = item_id
                writer.writerow(item)
        logger.info(f"ItemID сохранены в {output_file}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении CSV: {str(e)}")
        raise


def main():
    try:
        trading_api = EbayTradingAPI()
        time.sleep(1)
        print("=== eBay Listing Manager ===")
        print("1. Создать новые листинги из items.json")
        print("2. Обновить существующие листинги из output_items.json")
        print("3. Получить данные категории")
        choice = input("Выберите действие (1 или 2): ").strip()

        if choice == "1":
            # Проверяем службы доставки
            shipping_services = trading_api.get_shipping_services()
            logger.info(f"Поддерживаемые службы доставки: {shipping_services}")
            # Проверяем профили продавца
            profiles = trading_api.get_seller_profiles()
            if not profiles:
                logger.error("Не удалось получить профили продавца")
                raise Exception("Не удалось получить профили продавца")
            logger.info(f"Профили продавца: {profiles}")
            # Загружаем товары из JSON
            json_file = "items.json"
            items = load_items_from_json(json_file)
            item_ids = []
            for item in items:
                # Проверяем листинг
                trading_api.verify_add_fixed_price_item(item_data=item)
                # Создаем листинг
                item_id = trading_api.add_fixed_price_item(item_data=item)
                logger.info(f"Листинг создан, ItemID: {item_id}")
                print(f"Листинг создан, ItemID: {item_id}")
                item_ids.append(item_id)
            # Сохраняем ItemID в JSON
            save_item_ids_to_json(items, item_ids)
        elif choice == "2":
            # Обновляем листинги из JSON
            update_items_from_json(trading_api)
        elif choice == "3":
            # Обновляем листинги из JSON
            trading_api.get_category_specifics("169291")
        else:
            print("Неверный выбор. Пожалуйста, выберите 1 или 2.")
            logger.error(f"Неверный выбор действия: {choice}")
    except Exception as e:
        logger.error(f"Ошибка в процессе обработки листингов: {str(e)}")
        print(f"Ошибка: {str(e)}")


if __name__ == "__main__":
    main()
