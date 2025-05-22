# utils/monobank.py
import json

import aiohttp

from config.config import Config


class MonobankPayment:
    BASE_URL = "https://api.monobank.ua/api/merchant/invoice"

    def __init__(self, token=None):
        config = Config.load()
        self.token = token or config.monobank.token

    async def create_invoice(
        self, amount, order_id, redirect_url, webhook_url=None, description=None
    ):
        """
        Создание счета в Monobank

        :param amount: Сумма в минимальных единицах валюты (копейки)
        :param order_id: ID заказа в вашей системе
        :param redirect_url: URL, куда перенаправлять пользователя после оплаты
        :param webhook_url: URL для отправки уведомлений о статусе оплаты
        :param description: Описание платежа
        :return: Словарь с данными ответа API или None в случае ошибки
        """
        headers = {"X-Token": self.token, "Content-Type": "application/json"}

        payload = {
            "amount": amount,
            "ccy": 980,  # Код валюты UAH
            "merchantPaymInfo": {
                "reference": str(order_id),
                "destination": description or f"Оплата заказа #{order_id}",
            },
            "redirectUrl": redirect_url,
        }

        if webhook_url:
            payload["webHookUrl"] = webhook_url

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/create", headers=headers, json=payload
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        print(f"Ошибка при создании счета Monobank: {error_text}")
                        return None
        except Exception as e:
            print(f"Исключение при создании счета Monobank: {e}")
            return None

    async def get_invoice_status(self, invoice_id):
        """
        Получение статуса счета

        :param invoice_id: ID счета в системе Monobank
        :return: Словарь с данными о статусе или None в случае ошибки
        """
        headers = {"X-Token": self.token}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/status?invoiceId={invoice_id}", headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        print(
                            f"Ошибка при получении статуса счета Monobank: {error_text}"
                        )
                        return None
        except Exception as e:
            print(f"Исключение при получении статуса счета Monobank: {e}")
            return None
