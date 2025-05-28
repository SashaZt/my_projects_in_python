# telegram_manager.py
import asyncio
import re
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import json

import httpx
from telethon import TelegramClient, events
from telethon.sessions.sqlite import SQLiteSession
from configuration.config import API_HASH, API_ID, API_URL, SESSION_PATH
from configuration.logger_setup import logger


class MultiUserTelegramManager:
    def __init__(self):
        self.clients: Dict[str, TelegramClient] = {}  # phone -> client
        self.user_sessions: Dict[int, str] = {}  # user_id -> phone
        self.session_path = Path(SESSION_PATH)
        self.session_path.mkdir(exist_ok=True)
        
    async def add_user_session(self, user_id: int, phone: str, password: str = None) -> dict:
        """Добавляет новую сессию пользователя"""
        try:
            phone = self.validate_phone_number(phone)
            session_file = self.session_path / f"{phone}.session"
            
            # Создаем клиент для этого телефона
            client = TelegramClient(
                str(session_file),
                API_ID,
                API_HASH,
                connection_retries=None,
                retry_delay=1,
            )
            
            # Если сессия уже существует, просто подключаемся
            if session_file.exists():
                await client.start(phone=lambda: phone)
                logger.info(f"Подключен к существующей сессии для {phone}")
            else:
                # Новая авторизация
                await client.start(
                    phone=lambda: phone,
                    password=lambda: password if password else None,
                )
                logger.info(f"Создана новая сессия для {phone}")
            
            # Сохраняем клиент и привязку
            self.clients[phone] = client
            self.user_sessions[user_id] = phone
            
            # Настраиваем обработчики событий
            await self.setup_event_handlers(client, user_id, phone)
            
            return {
                "status": "success", 
                "message": f"Сессия для {phone} успешно добавлена",
                "user_id": user_id,
                "phone": phone
            }
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении сессии: {e}")
            return {"status": "error", "message": str(e)}
    
    async def setup_event_handlers(self, client: TelegramClient, user_id: int, phone: str):
        """Настраивает обработчики событий для клиента"""
        
        @client.on(events.NewMessage)
        async def handle_message(event):
            await self.process_message(event, user_id, phone)
        
        @client.on(events.MessageRead)
        async def handle_read(event):
            await self.process_message_read(event, user_id, phone)
    
    async def process_message(self, event, user_id: int, phone: str):
        """Обработка входящих/исходящих сообщений"""
        try:
            chat = await event.get_chat()
            me = await event.client.get_me()
            sender = await event.get_sender()
            
            recipient = chat if sender.id == me.id else me
            direction = "outbox" if sender.id == me.id else "inbox"
            
            message_data = {
                "crm_user_id": user_id,  # ID пользователя CRM
                "telegram_phone": phone,
                "sender": {
                    "name": f"{sender.first_name or ''} {sender.last_name or ''}".strip(),
                    "username": f"@{sender.username}" if sender.username else None,
                    "telegram_id": sender.id,
                    "phone": getattr(sender, "phone", None),
                },
                "recipient": {
                    "name": f"{recipient.first_name or ''} {recipient.last_name or ''}".strip(),
                    "username": f"@{recipient.username}" if recipient.username else None,
                    "telegram_id": recipient.id,
                    "phone": getattr(recipient, "phone", None),
                },
                "message": {
                    "text": event.text,
                    "message_id": event.id,
                    "is_reply": event.is_reply,
                    "reply_to": event.reply_to_msg_id if event.is_reply else None,
                    "read": False,
                    "direction": direction,
                    "created_at": event.date.isoformat(),
                },
            }
            
            await self.send_to_api(message_data, "/telegram/message")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения для {phone}: {e}")
    
    async def process_message_read(self, event, user_id: int, phone: str):
        """Обработка события прочтения сообщений"""
        try:
            if hasattr(event, "max_id") and event.max_id:
                me = await event.client.get_me()
                read_data = {
                    "crm_user_id": user_id,
                    "telegram_phone": phone,
                    "sender_id": me.id,
                    "recipient_id": me.id if event.chat_id == me.id else event.chat_id,
                    "max_id": event.max_id,
                }
                await self.send_to_api(read_data, "/telegram/message/read")
        except Exception as e:
            logger.error(f"Ошибка при обработке прочтения для {phone}: {e}")
    
    async def send_message(self, user_id: int, recipient_id: int, message_text: str) -> dict:
        """Отправка сообщения от имени пользователя CRM"""
        try:
            phone = self.user_sessions.get(user_id)
            if not phone:
                return {"status": "error", "message": "Пользователь не авторизован в Telegram"}
            
            client = self.clients.get(phone)
            if not client:
                return {"status": "error", "message": "Клиент не найден"}
            
            # Отправляем сообщение
            recipient = await client.get_entity(recipient_id)
            message = await client.send_message(recipient, message_text)
            
            # Получаем данные отправителя
            me = await client.get_me()
            
            # Формируем данные для API
            message_data = {
                "crm_user_id": user_id,
                "telegram_phone": phone,
                "sender": {
                    "name": f"{me.first_name or ''} {me.last_name or ''}".strip(),
                    "username": f"@{me.username}" if me.username else None,
                    "telegram_id": me.id,
                    "phone": getattr(me, "phone", None),
                },
                "recipient": {
                    "name": f"{recipient.first_name or ''} {recipient.last_name or ''}".strip(),
                    "username": f"@{recipient.username}" if recipient.username else None,
                    "telegram_id": recipient.id,
                    "phone": getattr(recipient, "phone", None),
                },
                "message": {
                    "text": message_text,
                    "message_id": message.id,
                    "is_reply": False,
                    "reply_to": None,
                    "read": False,
                    "direction": "outbox",
                    "created_at": message.date.isoformat(),
                },
            }
            
            await self.send_to_api(message_data, "/telegram/message")
            
            return {
                "status": "success", 
                "message": "Сообщение отправлено",
                "message_id": message.id
            }
            
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_user_chats(self, user_id: int) -> dict:
        """Получение списка чатов пользователя"""
        try:
            phone = self.user_sessions.get(user_id)
            if not phone:
                return {"status": "error", "message": "Пользователь не авторизован"}
            
            client = self.clients.get(phone)
            if not client:
                return {"status": "error", "message": "Клиент не найден"}
            
            dialogs = await client.get_dialogs()
            chats = []
            
            for dialog in dialogs:
                chat_info = {
                    "id": dialog.entity.id,
                    "title": dialog.title,
                    "type": type(dialog.entity).__name__,
                    "unread_count": dialog.unread_count,
                    "last_message_date": dialog.date.isoformat() if dialog.date else None,
                }
                chats.append(chat_info)
            
            return {"status": "success", "chats": chats}
            
        except Exception as e:
            logger.error(f"Ошибка при получении чатов: {e}")
            return {"status": "error", "message": str(e)}
    
    async def disconnect_user(self, user_id: int) -> dict:
        """Отключение пользователя"""
        try:
            phone = self.user_sessions.get(user_id)
            if phone and phone in self.clients:
                await self.clients[phone].disconnect()
                del self.clients[phone]
                del self.user_sessions[user_id]
                logger.info(f"Пользователь {user_id} ({phone}) отключен")
                return {"status": "success", "message": "Пользователь отключен"}
            return {"status": "error", "message": "Пользователь не найден"}
        except Exception as e:
            logger.error(f"Ошибка при отключении: {e}")
            return {"status": "error", "message": str(e)}
    
    async def disconnect_all(self):
        """Отключение всех клиентов"""
        for client in self.clients.values():
            try:
                await client.disconnect()
            except:
                pass
        self.clients.clear()
        self.user_sessions.clear()
        logger.info("Все клиенты отключены")
    
    def validate_phone_number(self, phone_number: str) -> str:
        """Валидация номера телефона"""
        if not re.match(r"^\+\d{10,15}$", phone_number):
            raise ValueError("Номер телефона должен быть в формате +1234567890.")
        return phone_number
    
    async def send_to_api(self, data: dict, endpoint: str = "/telegram/message"):
        """Отправка данных в API"""
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            try:
                url = f"{API_URL}{endpoint}"
                response = await client.post(url, json=data)
                response.raise_for_status()
                logger.info(f"Данные успешно отправлены в API")
                return True
            except httpx.HTTPError as e:
                logger.error(f"Ошибка HTTP при отправке данных: {e}")
            except Exception as e:
                logger.error(f"Ошибка при отправке данных: {e}")
            return False


# Глобальный менеджер
telegram_manager = MultiUserTelegramManager()


async def main():
    """Основная функция для запуска менеджера"""
    try:
        logger.info("Запуск многопользовательского Telegram менеджера...")
        
        # Здесь можно загрузить существующие сессии из БД
        # await load_existing_sessions()
        
        # Запускаем бесконечный цикл
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки...")
    finally:
        await telegram_manager.disconnect_all()
        logger.info("Менеджер остановлен")


if __name__ == "__main__":
    asyncio.run(main())