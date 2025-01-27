import asyncio
import re
from pathlib import Path

import httpx
from configuration.config import API_HASH, API_ID, API_URL, SESSION_PATH
from configuration.logger_setup import logger
from telethon import TelegramClient, events


def validate_phone_number(phone_number: str) -> str:
    if not re.match(r"^\+\d{10,15}$", phone_number):
        raise ValueError("Номер телефона должен быть в формате +1234567890.")
    return phone_number


def get_session_name() -> tuple[str, Path]:
    phone_number = input("Введите номер телефона (в формате +1234567890): ").strip()
    phone_number = validate_phone_number(phone_number)
    session_name = Path(SESSION_PATH) / f"{phone_number}.session"
    return phone_number, session_name


async def send_to_api(data: dict, part_url):
    async with httpx.AsyncClient(verify=False) as client:
        try:
            url = f"{API_URL}{part_url}"
            response = await client.post(url, json=data)
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
    """
    Обрабатывает входящие сообщения.
    """
    try:
        sender = await event.get_sender()
        recipient = await client.get_me()

        # Проверяем, является ли сообщение ответом
        is_reply = event.is_reply
        reply_to_msg_id = event.reply_to_msg_id if is_reply else None

        all_data = {
            "sender": {
                "name": f"{sender.first_name or ''} {sender.last_name or ''}".strip(),
                "username": f"@{sender.username}" if sender.username else None,
                "telegram_id": sender.id,
                "phone": getattr(sender, "phone", None),
                # "type": get_sender_type(sender),
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
                "is_reply": is_reply,
                "reply_to": reply_to_msg_id,
                "read": False,  # Сообщение считается непрочитанным по умолчанию
            },
        }

        logger.info(all_data)
        part_url = "/telegram/message"
        await send_to_api(all_data, part_url)

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")


@client.on(events.MessageRead)
async def handle_message_read(event):
    """
    Обрабатывает событие, когда сообщение становится прочитанным.
    """
    part_url = "/telegram/message/read"
    try:
        logger.info(f"Событие MessageRead: {event.to_dict()}")

        if hasattr(event, "max_id") and event.max_id:
            # Получаем текущего пользователя (отправителя)
            recipient = await client.get_me()

            # Формируем данные для API
            read_status = {
                "max_id": event.max_id,
                "read": True,
                "sender_id": recipient.id,  # ID отправителя
                "recipient_id": event.chat_id,  # ID чата или получателя
            }

            logger.info(f"Все сообщения до ID {event.max_id} помечены как прочитанные.")
            await send_to_api(read_status, part_url)
        else:
            logger.warning("Событие MessageRead не содержит max_id.")
    except Exception as e:
        logger.error(f"Ошибка при обработке события прочтения: {e}")


async def main():
    """
    Основная функция запуска клиента.
    """
    await client.start(phone=lambda: phone_number)
    logger.info("Клиент запущен. Ожидаем сообщения...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
