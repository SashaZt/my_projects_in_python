import json
from typing import Any, Dict, Optional

import requests
from config.config import TIKTOK_ACCOUNT_ID, TIKTOK_API_BASE_URL, TIKTOK_API_KEY
from config.logger import logger


class TikTokAlertsAPI:
    def __init__(
        self,
        base_url: str = TIKTOK_API_BASE_URL,
        api_key: str = TIKTOK_API_KEY,
        account_id: int = TIKTOK_ACCOUNT_ID,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.account_id = account_id
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }

    def create_alert(self, unique_id: str) -> Dict[str, Any]:
        """Создать новый Alert для TikTok аккаунта"""
        url = f"{self.base_url}/accounts/{self.account_id}/alerts/create?apiKey={self.api_key}"
        payload = {"unique_id": unique_id}

        logger.info(f"Создание Alert для {unique_id}...")
        response = requests.put(url, headers=self.headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_alerts(self) -> Dict[str, Any]:
        """Получить список всех Alerts"""
        url = f"{self.base_url}/accounts/{self.account_id}/alerts/list?apiKey={self.api_key}"

        logger.info("Получение списка Alerts...")
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def subscribe_to_alert(self, alert_id: int, webhook_url: str) -> Dict[str, Any]:
        """Подписаться на Alert, указав URL для получения уведомлений"""
        url = f"{self.base_url}/accounts/{self.account_id}/alerts/{alert_id}/targets/create?apiKey={self.api_key}"
        payload = {"url": webhook_url}

        logger.info(f"Подписка на Alert {alert_id} с webhook URL: {webhook_url}...")
        response = requests.put(url, headers=self.headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
