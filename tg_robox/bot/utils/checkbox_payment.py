import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
from config.logger import logger
from config.config import Config

class CheckboxPayment:
    def __init__(self):
        config = Config.load()
        self.base_url = config.checkbox.base_url
        self.license_key = config.checkbox.x_license_key
        self.pin_code = config.checkbox.pin_code
        self.terminal_id = config.checkbox.terminal_id
        self.device_id = config.checkbox.x_device_id
        self.client_name = config.checkbox.x_client_name
        self.client_version = config.checkbox.x_client_version
        self.token_file = Path("config/token.json")
        
    async def _get_headers(self, include_auth=False):
        """Получить базовые заголовки"""
        headers = {
            'Content-Type': 'application/json',
            'X-Client-Name': self.client_name,
            'X-Client-Version': self.client_version,
            'X-License-Key': self.license_key
        }
        
        if include_auth:
            token = await self._get_valid_token()
            if token:
                headers['Authorization'] = f'Bearer {token}'
            else:
                raise Exception("Не удалось получить токен авторизации")
                
        return headers
    
    async def _get_valid_token(self):
        """Получить действующий токен"""
        # Проверяем существующий токен
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                
                # Проверяем, не истек ли токен (добавляем простую проверку по времени)
                if 'created_at' in token_data:
                    created_at = datetime.fromisoformat(token_data['created_at'])
                    if datetime.now() - created_at < timedelta(hours=23):  # Токен действует 24 часа
                        return token_data['access_token']
            except Exception as e:
                logger.error(f"Ошибка при чтении токена: {e}")
        
        # Получаем новый токен
        return await self._refresh_token()
    
    async def _refresh_token(self):
        """Получить новый токен"""
        url = f"{self.base_url}/cashier/signinPinCode"
        headers = await self._get_headers()
        headers['X-Device-ID'] = self.device_id
        
        data = {"pin_code": self.pin_code}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        token_data['created_at'] = datetime.now().isoformat()
                        
                        # Сохраняем токен в файл
                        os.makedirs(self.token_file.parent, exist_ok=True)
                        with open(self.token_file, 'w') as f:
                            json.dump(token_data, f, indent=2)
                        
                        logger.info("Получен новый токен Checkbox")
                        return token_data['access_token']
                    else:
                        logger.error(f"Ошибка получения токена: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Ошибка при запросе токена: {e}")
            return None
    
    async def create_invoice(self, product_name: str, amount_kopecks: int, order_id: int):
        """Создать инвойс в Checkbox"""
        url = f"{self.base_url}/invoices/fiscalize"
        headers = await self._get_headers(include_auth=True)
        
        data = {
            "goods": [
                {
                    "good": {
                        "name": product_name,
                        "price": amount_kopecks,
                        "code": str(order_id)
                    },
                    "quantity": 1000,
                    "is_return": False
                }
            ],
            "payments": [
                {
                    "type": "CASHLESS",
                    "value": amount_kopecks,
                    "label": "Платіж через інтегратора MONOBANK",
                    "provider_type": "TERMINAL"
                }
            ],
            "terminal_id": self.terminal_id,
            "discounts": [],
            "bonuses": [],
            "validity": 150
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Сохраняем ответ в файл для отладки
                        invoice_file = Path(f"logs/invoice_{order_id}.json")
                        os.makedirs(invoice_file.parent, exist_ok=True)
                        with open(invoice_file, 'w') as f:
                            json.dump(result, f, indent=2)
                        
                        logger.info(f"Создан инвойс Checkbox: {result['id']}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка создания инвойса: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Ошибка при создании инвойса: {e}")
            return None
    
    async def check_invoice_status(self, invoice_id: str):
        """Проверить статус инвойса"""
        url = f"{self.base_url}/invoices/{invoice_id}"
        headers = await self._get_headers(include_auth=True)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Сохраняем статус в файл для отладки
                        status_file = Path(f"logs/status_{invoice_id}.json")
                        os.makedirs(status_file.parent, exist_ok=True)
                        with open(status_file, 'w') as f:
                            json.dump({
                                "status": result.get("status"),
                                "id": result.get("id"),
                                "created_at": result.get("created_at"),
                                "updated_at": result.get("updated_at"),
                                "checked_at": datetime.now().isoformat()
                            }, f, indent=2)
                        
                        return result
                    else:
                        logger.error(f"Ошибка проверки статуса: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса: {e}")
            return None