import asyncio
from pathlib import Path
import re
import httpx
from telethon import TelegramClient, events
from configuration.config import API_HASH, API_ID, API_URL, SESSION_PATH
from configuration.logger_setup import logger


def validate_phone_number(phone_number: str) -> str:
    if not re.match(r"^\+\d{10,15}$", phone_number):
        raise ValueError("Номер телефона должен быть в формате +1234567890.")
    return phone_number


def get_session_name() -> tuple[str, Path]:
    phone_number = input("Введите номер телефона (в формате +1234567890): ").strip()
    phone_number = validate_phone_number(phone_number)
    session_name = Path(SESSION_PATH) / f"{phone_number}.session"
    return phone_number, session_name


async def send_to_api(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.post(API_URL, json=data)
            response.raise_for_status()
            logger.info(f"Данные успешно отправлены: {response.json()}")
        except httpx.HTTPError as e:
            logger.error(f"Ошибка при отправке данных на API: {e}")


def get_sender_type(sender) -> str:
    if sender.bot:
        return "bot"
    elif sender.id < 0:
        if sender.is_channel:
            return "channel"
        elif sender.is_group:
            return "group"
    return "user"


phone_number, session_name = get_session_name()
client = TelegramClient(str(session_name), API_ID, API_HASH)


@client.on(events.NewMessage)
async def handle_message(event):
    try:
        sender = await event.get_sender()
        recipient = await client.get_me()

        all_data = {
            "sender": {
                "name": f"{sender.first_name or ''} {sender.last_name or ''}".strip(),
                "username": f"@{sender.username}" if sender.username else None,
                "telegram_id": sender.id,
                "phone": getattr(sender, "phone", None)
            },
            "recipient": {
                "name": f"{recipient.first_name or ''} {recipient.last_name or ''}".strip(),
                "username": f"@{recipient.username}" if recipient.username else None,
                "telegram_id": recipient.id,
                "phone": getattr(recipient, "phone", None)
            },
            "message": {
                "text": event.text
            }
        }
        print(all_data)
        logger.info(f"Отправляем данные: {all_data}")
        await send_to_api(all_data)

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")


async def main():
    await client.start(phone=lambda: phone_number)
    logger.info("Клиент запущен. Ожидаем сообщения...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
