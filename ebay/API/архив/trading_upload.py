import json
import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
from auth import EbayAuth
from logger import logger

from config import CLIENT_ID, CLIENT_SECRET, DEV_ID, RUNAME


class EbayTradingClient:
    def __init__(self):
        self.auth = EbayAuth(CLIENT_ID, CLIENT_SECRET)
        self.base_url = "https://api.sandbox.ebay.com/ws/api.dll"
        self.access_token = None

        # Попытка аутентификации
        self.authenticate()

    def authenticate(self):
        """Аутентификация с использованием существующего токена или обновление через refresh token"""
        if hasattr(self.auth, "user_token") and self.auth.user_token:
            self.access_token = self.auth.user_token.get("access_token")
            logger.info("Используется существующий токен.")
            return True

        # Проверка наличия refresh токена
        if hasattr(self.auth, "refresh_token") and self.auth.refresh_token:
            logger.info("Обновление токена через refresh token.")
            token_data = self.auth.refresh_user_token()
            if token_data:
                self.access_token = token_data.get("access_token")
                return True

        # Запрос нового токена через авторизацию
        auth_url = self.auth.get_authorization_url(
            [
                "https://api.ebay.com/oauth/api_scope",
                "https://api.ebay.com/oauth/api_scope/sell.inventory",
                "https://api.ebay.com/oauth/api_scope/sell.marketing",
                "https://api.ebay.com/oauth/api_scope/sell.account",
            ]
        )

        if auth_url:
            logger.info(f"Перейдите по ссылке для авторизации: {auth_url}")
            auth_code = input("Введите код авторизации: ")
            token_data = self.auth.get_user_token(auth_code)
            if token_data:
                self.access_token = token_data.get("access_token")
                return True

        return False

    def add_item(self, product_data):
        """Добавление товара через Trading API"""
        timestamp = int(time.time())
        unique_sku = f"LAPTOP-{timestamp}"

        headers = {
            "X-EBAY-API-SITEID": "77",  # Германия
            "X-EBAY-API-COMPATIBILITY-LEVEL": "1211",
            "X-EBAY-API-CALL-NAME": "AddItem",
            "X-EBAY-API-IAF-TOKEN": self.access_token,
            "Content-Type": "text/xml",
        }

        # Формирование XML запроса
        xml_request = f"""<?xml version="1.0" encoding="utf-8"?>
<AddItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <RequesterCredentials>
    <eBayAuthToken>{self.access_token}</eBayAuthToken>
  </RequesterCredentials>
  <ErrorLanguage>en_US</ErrorLanguage>
  <WarningLevel>High</WarningLevel>
  <Item>
    <Title>{product_data.get('title', '')}</Title>
    <Description>{product_data.get('description', '')}</Description>
    <PrimaryCategory>
      <CategoryID>177</CategoryID>
    </PrimaryCategory>
    <StartPrice>{product_data.get('price', {}).get('value', 0)}</StartPrice>
    <CategoryMappingAllowed>true</CategoryMappingAllowed>
    <ConditionID>3000</ConditionID>
    <Country>DE</Country>
    <Currency>EUR</Currency>
    <DispatchTimeMax>3</DispatchTimeMax>
    <ListingDuration>GTC</ListingDuration>
    <ListingType>FixedPriceItem</ListingType>
    <PaymentMethods>PayPal</PaymentMethods>
    <PayPalEmailAddress>test-paypal@test.com</PayPalEmailAddress>
    <PictureDetails>
      <PictureURL>{product_data.get('images', [''])[0]}</PictureURL>
    </PictureDetails>
    <PostalCode>10115</PostalCode>
    <Quantity>1</Quantity>
    <ReturnPolicy>
      <ReturnsAcceptedOption>ReturnsAccepted</ReturnsAcceptedOption>
      <RefundOption>MoneyBack</RefundOption>
      <ReturnsWithinOption>Days_30</ReturnsWithinOption>
      <ShippingCostPaidByOption>Seller</ShippingCostPaidByOption>
    </ReturnPolicy>
    <ShippingDetails>
      <ShippingType>Flat</ShippingType>
      <ShippingServiceOptions>
        <ShippingServicePriority>1</ShippingServicePriority>
        <ShippingService>DE_DHLPaket</ShippingService>
        <ShippingServiceCost currencyID="EUR">5.99</ShippingServiceCost>
      </ShippingServiceOptions>
    </ShippingDetails>
    <Site>Germany</Site>
  </Item>
</AddItemRequest>"""

        # Отправка запроса
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                data=xml_request.encode("utf-8"),
                timeout=30,
            )
            response.raise_for_status()

            # Парсинг ответа
            root = ET.fromstring(response.content)
            namespace = {"ns": "urn:ebay:apis:eBLBaseComponents"}

            ack = root.find(".//ns:Ack", namespace)
            if ack is not None and ack.text == "Success":
                item_id = root.find(".//ns:ItemID", namespace)
                if item_id is not None:
                    logger.info(f"Товар успешно добавлен на eBay, ID: {item_id.text}")
                    return item_id.text

            # В случае ошибки
            error_message = root.find(".//ns:Errors/ns:ShortMessage", namespace)
            if error_message is not None:
                logger.error(f"Ошибка при добавлении товара: {error_message.text}")
                long_message = root.find(".//ns:Errors/ns:LongMessage", namespace)
                if long_message is not None:
                    logger.error(f"Подробное описание: {long_message.text}")

            logger.error(f"Не удалось добавить товар. Ответ: {response.text}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при добавлении товара: {e}")
            return None


def load_product_data(file_path):
    """Загрузка данных товара из JSON файла"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных товара: {e}")
        return None


def upload_product():
    """Основная функция для выгрузки товара"""
    # Загрузка данных товара
    product_data = load_product_data("product_template.json")
    if not product_data:
        logger.error("Не удалось загрузить данные товара")
        return False

    # Инициализация клиента
    client = EbayTradingClient()

    # Добавление товара
    item_id = client.add_item(product_data)
    if not item_id:
        return False

    logger.info(f"Товар успешно опубликован на eBay! ID объявления: {item_id}")
    return True


if __name__ == "__main__":
    if upload_product():
        logger.info("Выгрузка товара завершена успешно!")
    else:
        logger.error("Не удалось выгрузить товар.")
