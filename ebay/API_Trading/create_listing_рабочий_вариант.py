import base64
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

import requests
from logger import logger
from token_storage import TokenStorage

from config import (
    CLIENT_ID,
    CLIENT_SECRET,
    DEFAULT_MARKETPLACE_ID,
    RUNAME,
    TOKEN_URL,
    USER_SCOPES,
)

# Trading API endpoint для Sandbox
API_ENDPOINT = "https://api.sandbox.ebay.com/ws/api.dll"


class EbayAuth:
    def __init__(self, client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_storage = TokenStorage()
        self.user_token = None
        self.user_token_expiry = None
        self.refresh_token = self.token_storage.get_refresh_token()
        self.refresh_token_expiry = self.token_storage.get_expiry_time()

        if self.token_storage.is_access_token_valid():
            self.user_token = self.token_storage.get_access_token()
            self.user_token_expiry = self.token_storage.get_expiry_time()
            logger.info("Восстановлен существующий токен из хранилища")
        else:
            logger.warning("Токен отсутствует или истек. Требуется обновление.")

    def _encode_credentials(self):
        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()

    def refresh_user_token(self):
        if not self.refresh_token:
            logger.error("Refresh токен отсутствует.")
            return None

        if self.refresh_token_expiry and datetime.now() > self.refresh_token_expiry:
            logger.error("Refresh токен истек. Требуется повторная авторизация.")
            return None

        logger.info("Обновление User токена")
        headers = {
            "Authorization": f"Basic {self._encode_credentials()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "refresh_token", "refresh_token": self.refresh_token}

        try:
            response = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            logger.info(f"Получен новый токен: {token_data}")
            self.token_storage.update_tokens(token_data)
            self.user_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 7200)
            self.user_token_expiry = datetime.now() + timedelta(seconds=expires_in)
            logger.info(
                f"User токен обновлен, действителен до: {self.user_token_expiry}"
            )
            return token_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при обновлении токена: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Ответ сервера: {e.response.text}")
            return None


class EbayTradingAPI:
    def __init__(self):
        self.auth = EbayAuth()
        self.token = self.auth.user_token

        if (
            not self.auth.user_token
            or not self.auth.token_storage.is_access_token_valid()
        ):
            logger.info("Токен истек или отсутствует. Пытаемся обновить.")
            token_data = self.auth.refresh_user_token()
            if token_data:
                self.token = token_data.get("access_token")
            else:
                raise Exception("Не удалось обновить токен.")

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

    def verify_add_item(self, item_data=None):
        """Проверка листинга с помощью VerifyAddItem."""
        headers = {
            "Content-Type": "text/xml",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "X-EBAY-API-CALL-NAME": "VerifyAddItem",
            "X-EBAY-API-SITEID": "77",
            "X-EBAY-API-IAF-TOKEN": self.token,
        }
        xml_request = self._build_item_xml(item_data)
        try:
            logger.info("Отправка запроса VerifyAddItem")
            response = requests.post(API_ENDPOINT, headers=headers, data=xml_request)
            logger.info(f"Ответ сервера VerifyAddItem: {response.text}")
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                namespaces = {"ns": "urn:ebay:apis:eBLBaseComponents"}
                ack = root.find(".//ns:Ack", namespaces)
                if ack is None:
                    logger.error(f"Элемент Ack не найден в ответе: {response.text}")
                    raise Exception(
                        f"Неверный формат ответа VerifyAddItem: {response.text}"
                    )
                if ack.text == "Success":
                    logger.info("Листинг прошел проверку VerifyAddItem")
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
                    raise Exception(f"Ошибка VerifyAddItem: {error_messages}")
            else:
                logger.error(
                    f"Ошибка VerifyAddItem: {response.status_code} - {response.text}"
                )
                raise Exception(f"Ошибка VerifyAddItem: {response.text}")
        except Exception as e:
            logger.error(f"Исключение при проверке листинга: {str(e)}")
            raise

    def add_item(self, item_data=None):
        """Создание листинга с помощью AddItem."""
        headers = {
            "Content-Type": "text/xml",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "X-EBAY-API-CALL-NAME": "AddItem",
            "X-EBAY-API-SITEID": "77",
            "X-EBAY-API-IAF-TOKEN": self.token,
        }
        xml_request = self._build_add_item_xml(item_data)
        try:
            logger.info("Отправка запроса AddItem")
            response = requests.post(API_ENDPOINT, headers=headers, data=xml_request)
            logger.info(f"Ответ сервера AddItem: {response.text}")
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                namespaces = {"ns": "urn:ebay:apis:eBLBaseComponents"}
                ack = root.find(".//ns:Ack", namespaces)
                if ack is None:
                    logger.error(f"Элемент Ack не найден в ответе: {response.text}")
                    raise Exception(f"Неверный формат ответа AddItem: {response.text}")
                if ack.text == "Success":
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
                    raise Exception(f"Ошибка AddItem: {error_messages}")
            else:
                logger.error(
                    f"Ошибка AddItem: {response.status_code} - {response.text}"
                )
                raise Exception(f"Ошибка AddItem: {response.text}")
        except Exception as e:
            logger.error(f"Исключение при создании листинга: {str(e)}")
            raise

    def revise_item(self, item_id, item_data=None):
        """Обновление листинга с помощью ReviseItem."""
        headers = {
            "Content-Type": "text/xml",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "X-EBAY-API-CALL-NAME": "ReviseItem",
            "X-EBAY-API-SITEID": "77",
            "X-EBAY-API-IAF-TOKEN": self.token,
        }
        xml_request = self._build_revise_item_xml(item_id, item_data)
        try:
            logger.info(f"Отправка запроса ReviseItem для ItemID: {item_id}")
            logger.debug(f"XML запрос ReviseItem: {xml_request}")
            response = requests.post(API_ENDPOINT, headers=headers, data=xml_request)
            logger.info(f"Ответ сервера ReviseItem: {response.text}")
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                namespaces = {"ns": "urn:ebay:apis:eBLBaseComponents"}
                ack = root.find(".//ns:Ack", namespaces)
                if ack is None:
                    logger.error(f"Элемент Ack не найден в ответе: {response.text}")
                    raise Exception(
                        f"Неверный формат ответа ReviseItem: {response.text}"
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
                    raise Exception(f"Ошибка ReviseItem: {error_messages}")
            else:
                logger.error(
                    f"Ошибка ReviseItem: {response.status_code} - {response.text}"
                )
                raise Exception(f"Ошибка ReviseItem: {response.text}")
        except Exception as e:
            logger.error(f"Исключение при обновлении листинга: {str(e)}")
            raise

    def _build_item_xml(self, item_data=None):
        """Формирование XML для проверки листинга."""
        item_data = item_data or {}
        title = item_data.get("Title", "Designer Women's Handbag - Black Leather")
        description = item_data.get(
            "Description",
            "Elegant black leather handbag, perfect for daily use. Brand new, high quality.",
        )
        price = item_data.get("Price", "50.00")
        quantity = item_data.get("Quantity", "1")
        color = item_data.get("Color", "Schwarz")
        material = item_data.get("Material", "Echtleder")
        style = item_data.get("Style", "Schultertasche")
        image_url = item_data.get("ImageURL", "https://example.com/handbag.jpg")
        profiles = self.get_seller_profiles() or {}
        shipping_profile_id = profiles.get("shipping_id", "6208596000")
        return_profile_id = profiles.get("return_id", "6208750000")
        payment_profile_id = profiles.get("payment_id", "6208882000")
        return f"""<?xml version="1.0" encoding="utf-8"?>
        <VerifyAddItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
            <Item>
                <Title>{title}</Title>
                <Description>{description}</Description>
                <PrimaryCategory>
                    <CategoryID>169291</CategoryID>
                </PrimaryCategory>
                <StartPrice currencyID="EUR">{price}</StartPrice>
                <ConditionID>1000</ConditionID>
                <Country>DE</Country>
                <Currency>EUR</Currency>
                <DispatchTimeMax>3</DispatchTimeMax>
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
                        <Value>Handmade</Value>
                    </NameValueList>
                    <NameValueList>
                        <Name>Abteilung</Name>
                        <Value>Damen</Value>
                    </NameValueList>
                </ItemSpecifics>
                <ProductListingDetails>
                    <EAN>Nicht zutreffend</EAN>
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
                <PostalCode>10115</PostalCode>
                <Quantity>{quantity}</Quantity>
                <Site>Germany</Site>
            </Item>
        </VerifyAddItemRequest>"""

    def _build_add_item_xml(self, item_data=None):
        """Формирование XML для AddItem."""
        item_data = item_data or {}
        title = item_data.get("Title", "Designer Women's Handbag - Black Leather")
        description = item_data.get(
            "Description",
            "Elegant black leather handbag, perfect for daily use. Brand new, high quality.",
        )
        price = item_data.get("Price", "50.00")
        quantity = item_data.get("Quantity", "1")
        color = item_data.get("Color", "Schwarz")
        material = item_data.get("Material", "Echtleder")
        style = item_data.get("Style", "Schultertasche")
        image_url = item_data.get("ImageURL", "https://example.com/handbag.jpg")
        profiles = self.get_seller_profiles() or {}
        shipping_profile_id = profiles.get("shipping_id", "6208596000")
        return_profile_id = profiles.get("return_id", "6208750000")
        payment_profile_id = profiles.get("payment_id", "6208882000")
        return f"""<?xml version="1.0" encoding="utf-8"?>
        <AddItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
            <Item>
                <Title>{title}</Title>
                <Description>{description}</Description>
                <PrimaryCategory>
                    <CategoryID>169291</CategoryID>
                </PrimaryCategory>
                <StartPrice currencyID="EUR">{price}</StartPrice>
                <ConditionID>1000</ConditionID>
                <Country>DE</Country>
                <Currency>EUR</Currency>
                <DispatchTimeMax>3</DispatchTimeMax>
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
                        <Value>Handmade</Value>
                    </NameValueList>
                    <NameValueList>
                        <Name>Abteilung</Name>
                        <Value>Damen</Value>
                    </NameValueList>
                </ItemSpecifics>
                <ProductListingDetails>
                    <EAN>Nicht zutreffend</EAN>
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
                <PostalCode>10115</PostalCode>
                <Quantity>{quantity}</Quantity>
                <Site>Germany</Site>
            </Item>
        </AddItemRequest>"""

    def _build_revise_item_xml(self, item_id, item_data=None):
        """Формирование XML для ReviseItem."""
        item_data = item_data or {}
        title = item_data.get("Title", "Designer Women's Handbag - Black Leather")
        description = item_data.get(
            "Description",
            "Elegant black leather handbag, perfect for daily use. Brand new, high quality.",
        )
        price = item_data.get("Price", "50.00")
        quantity = item_data.get("Quantity", "1")
        color = item_data.get("Color", "Schwarz")
        material = item_data.get("Material", "Echtleder")
        style = item_data.get("Style", "Schultertasche")
        image_url = item_data.get("ImageURL", "https://example.com/handbag.jpg")
        profiles = self.get_seller_profiles() or {}
        shipping_profile_id = profiles.get("shipping_id", "6208596000")
        return_profile_id = profiles.get("return_id", "6208750000")
        payment_profile_id = profiles.get("payment_id", "6208882000")
        return f"""<?xml version="1.0" encoding="utf-8"?>
        <ReviseItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
            <Item>
                <ItemID>{item_id}</ItemID>
                <Title>{title}</Title>
                <Description>{description}</Description>
                <StartPrice currencyID="EUR">{price}</StartPrice>
                <Quantity>{quantity}</Quantity>
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
                        <Value>Handmade</Value>
                    </NameValueList>
                    <NameValueList>
                        <Name>Abteilung</Name>
                        <Value>Damen</Value>
                    </NameValueList>
                </ItemSpecifics>
                <ProductListingDetails>
                    <EAN>Nicht zutreffend</EAN>
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
            </Item>
        </ReviseItemRequest>"""


def main():
    try:
        trading_api = EbayTradingAPI()
        # Проверяем службы доставки
        shipping_services = trading_api.get_shipping_services()
        logger.info(f"Поддерживаемые службы доставки: {shipping_services}")
        # Проверяем профили продавца
        profiles = trading_api.get_seller_profiles()
        if not profiles:
            logger.error("Не удалось получить профили продавца")
            raise Exception("Не удалось получить профили продавца")
        logger.info(f"Профили продавца: {profiles}")
        # Проверяем листинг
        trading_api.verify_add_item()
        # Создаем листинг
        item_id = trading_api.add_item()
        logger.info(f"Листинг создан, ItemID: {item_id}")
        print(f"Листинг создан, ItemID: {item_id}")
        # Пример обновления существующего листинга
        updated_data = {
            "Title": "GUCCI Tote Bag Soho Cellarius Gold Biege Leather Interlocking Authentic",
            "Description": "GUCCI Tote Bag Soho Cellarius Gold Biege Leather Interlocking Authentic",
            "Price": "420",
            "Quantity": "2",
            "Color": "Beige",
            "Material": "leather",
            "Style": "Tote",
            "ImageURL": "https://f.media-amazon.com/images/I/81zb7kDasbL._AC_SY575_.jpg",
        }
        revised_item_id = trading_api.revise_item(
            item_id="110586929006", item_data=updated_data
        )
        logger.info(f"Листинг обновлен, ItemID: {revised_item_id}")
        print(f"Листинг обновлен, ItemID: {revised_item_id}")
    except Exception as e:
        logger.error(f"Ошибка в процессе обновления листинга: {str(e)}")
        print(f"Не удалось обновить листинг: {str(e)}")


if __name__ == "__main__":
    main()
