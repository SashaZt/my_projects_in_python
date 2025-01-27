import asyncio
import re
from pathlib import Path

import httpx
from configuration.config import API_HASH, API_ID, API_URL, SESSION_PATH
from configuration.logger_setup import logger
from telethon import TelegramClient, events


class TelegramListener:
    def __init__(self, session_path, api_id, api_hash, api_url):
        self.client = None
        self.session_path = session_path
        self.api_id = api_id
        self.api_hash = api_hash
        self.api_url = api_url

    async def send_to_api(self, data: dict, endpoint: str = "/telegram/message"):
        async with httpx.AsyncClient(verify=False) as client:
            try:
                url = f"{self.api_url}{endpoint}"
                logger.info(f"URL: {url}")
                logger.info(f"Отправляем данные: {data}")
                response = await client.post(url, json=data)
                response.raise_for_status()
                logger.info(f"Данные успешно отправлены: {response.json()}")
            except httpx.HTTPError as e:
                logger.error(f"Ошибка при отправке данных на API: {e}")

    async def start(self, phone_number):
        self.client = TelegramClient(
            str(self.session_path / f"{phone_number}.session"),
            self.api_id,
            self.api_hash,
        )
        await self.client.start(phone=lambda: phone_number)
        await self.setup_handlers()
        logger.info("Listener запущен. Ожидаем сообщения...")

    async def setup_handlers(self):
        @self.client.on(events.NewMessage)
        async def handle_message(event):
            try:
                chat = await event.get_chat()
                me = await self.client.get_me()
                sender = await event.get_sender()

                logger.info(f"Chat info: {chat}")
                logger.info(f"Sender: {sender}")
                logger.info(f"Me: {me}")

                # Определяем получателя для личного чата
                recipient = chat if sender.id == me.id else me

                # Определяем направление сообщения
                direction = "outbox" if sender.id == me.id else "inbox"

                all_data = {
                    "sender": {
                        "name": f"{sender.first_name or ''} {sender.last_name or ''}".strip(),
                        "username": f"@{sender.username}" if sender.username else None,
                        "telegram_id": sender.id,
                        "phone": getattr(sender, "phone", None),
                    },
                    "recipient": {
                        "name": f"{recipient.first_name or ''} {recipient.last_name or ''}".strip(),
                        "username": (
                            f"@{recipient.username}" if recipient.username else None
                        ),
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

                logger.info(
                    f"Direction check - sender_id: {sender.id}, me_id: {me.id}, direction: {direction}"
                )
                logger.info(f"Отправляем данные: {all_data}")
                await self.send_to_api(all_data)

            except Exception as e:
                logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)

        @self.client.on(events.MessageRead)
        async def handle_message_read(event):
            try:
                logger.info(f"Событие MessageRead: {event.to_dict()}")

                if hasattr(event, "max_id") and event.max_id:
                    me = await self.client.get_me()
                    read_data = {
                        "sender_id": me.id,
                        "recipient_id": (
                            me.id if event.chat_id == me.id else event.chat_id
                        ),
                        "max_id": event.max_id,
                    }

                    logger.info(f"Данные о прочтении: {read_data}")
                    await self.send_to_api(read_data, "/telegram/message/read")
                else:
                    logger.warning("Событие MessageRead не содержит max_id")

            except Exception as e:
                logger.error(f"Ошибка при обработке события прочтения: {e}")

    async def run(self):
        await self.client.run_until_disconnected()


class TelegramSender:
    def __init__(self, session_path, api_id, api_hash, api_url):
        self.client = None
        self.session_path = session_path
        self.api_id = api_id
        self.api_hash = api_hash
        self.api_url = api_url

    async def start(self, phone_number):
        self.client = TelegramClient(
            str(self.session_path / f"{phone_number}.session"),
            self.api_id,
            self.api_hash,
        )
        await self.client.start(phone=lambda: phone_number)
        logger.info("Sender запущен")

    async def send_message(self, recipient_id, text, reply_to=None):
        try:
            message = await self.client.send_message(
                recipient_id, text, reply_to=reply_to
            )

            me = await self.client.get_me()
            recipient = await self.client.get_entity(recipient_id)

            # Формируем данные для API
            message_data = {
                "sender": {
                    "name": f"{me.first_name or ''} {me.last_name or ''}".strip(),
                    "username": f"@{me.username}" if me.username else None,
                    "telegram_id": me.id,
                    "phone": getattr(me, "phone", None),
                },
                "recipient": {
                    "name": f"{recipient.first_name or ''} {recipient.last_name or ''}".strip(),
                    "username": (
                        f"@{recipient.username}" if recipient.username else None
                    ),
                    "telegram_id": recipient.id,
                    "phone": getattr(recipient, "phone", None),
                },
                "message": {
                    "text": text,
                    "message_id": message.id,
                    "is_reply": bool(reply_to),
                    "reply_to": reply_to,
                    "read": False,
                    "direction": "outbox",
                },
            }

            await self.send_to_api(message_data)
            return message

        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            raise

    async def send_to_api(self, data: dict, endpoint: str = "/telegram/message"):
        # тот же метод, что и в TelegramListener
        async with httpx.AsyncClient(verify=False) as client:
            try:
                url = f"{self.api_url}{endpoint}"
                logger.info(f"URL: {url}")
                logger.info(f"Отправляем данные: {data}")
                response = await client.post(url, json=data)
                response.raise_for_status()
                logger.info(f"Данные успешно отправлены: {response.json()}")
            except httpx.HTTPError as e:
                logger.error(f"Ошибка при отправке данных на API: {e}")


class TelegramCRM:
    def __init__(self, config):
        self.config = config
        self.listener = TelegramListener(
            config.SESSION_PATH, config.API_ID, config.API_HASH, config.API_URL
        )
        self.sender = TelegramSender(
            config.SESSION_PATH, config.API_ID, config.API_HASH, config.API_URL
        )

    @staticmethod
    def validate_phone_number(phone_number: str) -> str:
        if not re.match(r"^\+\d{10,15}$", phone_number):
            raise ValueError("Номер телефона должен быть в формате +1234567890")
        return phone_number

    async def start(self, phone_number):
        # Запускаем слушателя в отдельной таске
        listener_task = asyncio.create_task(self.start_listener(phone_number))

        # Запускаем отправителя
        await self.sender.start(phone_number)

        return listener_task

    async def start_listener(self, phone_number):
        await self.listener.start(phone_number)
        await self.listener.run()

    async def send_message(self, recipient_id, text, reply_to=None):
        return await self.sender.send_message(recipient_id, text, reply_to)


async def main():

    # Показываем доступные сессии
    sessions = list(SESSION_PATH.glob("*.session"))
    if sessions:
        print("Доступные сессии:")
        for i, session in enumerate(sessions, 1):
            print(f"{i}. {session.stem}")
        choice = input("Выберите номер сессии или введите новый номер телефона: ")

        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(sessions):
                phone_number = sessions[choice_idx].stem
            else:
                phone_number = input(
                    "Введите номер телефона (в формате +1234567890): "
                ).strip()
        except ValueError:
            phone_number = choice.strip()
    else:
        print("Нет сохраненных сессий")
        phone_number = input("Введите номер телефона (в формате +1234567890): ").strip()

    crm = TelegramCRM(config)
    listener_task = await crm.start(phone_number)

    # Пример отправки сообщения
    recipient_id = input("Введите ID получателя: ").strip()
    await crm.send_message(recipient_id, "Тестовое сообщение")

    # Ожидаем работу слушателя
    await listener_task


if __name__ == "__main__":
    asyncio.run(main())
