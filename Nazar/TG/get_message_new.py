import asyncio
import re
from pathlib import Path

import httpx
from configuration.config import API_HASH, API_ID, API_URL, SESSION_PATH
from configuration.logger_setup import logger
from telethon import TelegramClient, events
from telethon.sessions.sqlite import SQLiteSession


class LockedSQLiteSession(SQLiteSession):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = asyncio.Lock()

    async def _update_session_table(self, *args, **kwargs):
        async with self._lock:
            await super()._update_session_table(*args, **kwargs)


def validate_phone_number(phone_number: str) -> str:
    if not re.match(r"^\+\d{10,15}$", phone_number):
        raise ValueError("Номер телефона должен быть в формате +1234567890.")
    return phone_number


def get_session_name() -> tuple[str, Path]:
    phone_number = input("Введите номер телефона (в формате +1234567890): ").strip()
    phone_number = validate_phone_number(phone_number)
    session_name = Path(SESSION_PATH) / f"{phone_number}.session"
    return phone_number, session_name


async def send_to_api(data: dict, endpoint: str = "/telegram/message"):
    async with httpx.AsyncClient(verify=False) as client:
        try:
            url = f"{API_URL}{endpoint}"
            # logger.info(f"URL: {url}")
            response = await client.post(url, json=data)
            response.raise_for_status()
            logger.info(f"Данные успешно отправлены: {response.json()}")
        except httpx.HTTPError as e:
            logger.error(f"Ошибка при отправке данных на API: {e}")


phone_number, session_name = get_session_name()
client = TelegramClient(LockedSQLiteSession(str(session_name)), API_ID, API_HASH)


@client.on(events.NewMessage)
async def handle_message(event):
    try:
        chat = await event.get_chat()
        me = await client.get_me()
        sender = await event.get_sender()

        # logger.info(f"Chat info: {chat}")
        # logger.info(f"Sender: {sender}")
        # logger.info(f"Me: {me}")

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

        logger.info(
            f"Direction check - sender_id: {sender.id}, me_id: {me.id}, direction: {direction}"
        )
        logger.info(f"Отправляем данные: {all_data}")
        await send_to_api(all_data)

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)


@client.on(events.MessageRead)
async def handle_message_read(event):
    try:
        # logger.info(f"Событие MessageRead: {event.to_dict()}")

        if hasattr(event, "max_id") and event.max_id:
            me = await client.get_me()
            read_data = {
                "sender_id": me.id,
                "recipient_id": me.id if event.chat_id == me.id else event.chat_id,
                "max_id": event.max_id,
            }

            logger.info(f"Данные о прочтении: {read_data}")
            await send_to_api(read_data, "/telegram/message/read")
        else:
            logger.warning("Событие MessageRead не содержит max_id")

    except Exception as e:
        logger.error(f"Ошибка при обработке события прочтения: {e}")


async def main():
    await client.start(phone=lambda: phone_number)
    logger.info("Клиент запущен. Ожидаем сообщения...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
