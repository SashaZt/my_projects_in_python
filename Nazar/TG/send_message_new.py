# Рабочий код от 07032025
import asyncio
import re
from pathlib import Path

import httpx
from configuration.config import API_HASH, API_ID, API_URL, SESSION_PATH
from configuration.logger_setup import logger
from telethon import TelegramClient


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


def validate_phone_number(phone_number: str) -> str:
    if not re.match(r"^\+\d{10,15}$", phone_number):
        raise ValueError("Номер телефона должен быть в формате +1234567890.")
    return phone_number


async def main():
    # Показываем доступные сессии
    session_path = Path(SESSION_PATH)
    sessions = list(session_path.glob("*.session"))
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
                phone_number = validate_phone_number(phone_number)
        except ValueError:
            phone_number = validate_phone_number(choice.strip())
    else:
        print("Нет сохраненных сессий")
        phone_number = input("Введите номер телефона (в формате +1234567890): ").strip()
        phone_number = validate_phone_number(phone_number)

    session_name = session_path / f"{phone_number}.session"
    client = TelegramClient(
        str(session_name),
        API_ID,
        API_HASH,
        connection_retries=None,  # Бесконечные попытки переподключения
        retry_delay=1,  # Задержка между попытками в секундах
    )

    try:
        await client.start(phone=lambda: phone_number)
        logger.info("Клиент запущен. Готов к отправке сообщений...")

        print(
            "\nДля отправки сообщения введите команду в формате: send ID_получателя текст_сообщения"
        )
        print("Для выхода введите: exit")

        while True:
            command = input("> ").strip()

            if command.lower() == "exit":
                break

            if command.startswith("send "):
                try:
                    parts = command.split(" ", 2)
                    if len(parts) < 3:
                        print(
                            "Ошибка: Используйте формат: send ID_получателя текст_сообщения"
                        )
                        continue

                    _, recipient_id, message_text = parts

                    try:
                        recipient_id = int(recipient_id)
                    except ValueError:
                        print("Ошибка: ID получателя должен быть числом")
                        continue

                    if not message_text:
                        print("Ошибка: введите текст сообщения")
                        continue

                    try:
                        recipient = await client.get_entity(recipient_id)
                        message = await client.send_message(recipient, message_text)

                        me = await client.get_me()
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
                                    f"@{recipient.username}"
                                    if recipient.username
                                    else None
                                ),
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
                            },
                        }

                        await send_to_api(message_data)
                        print("Сообщение отправлено")
                    except ValueError as e:
                        print(f"Ошибка: Пользователь не найден - {e}")
                    except Exception as e:
                        print(f"Ошибка при отправке: {e}")
                except Exception as e:
                    print(f"Ошибка: {e}")
            else:
                print(
                    "Неизвестная команда. Используйте: send ID_получателя текст_сообщения"
                )
    except KeyboardInterrupt:
        print("\nПрограмма остановлена пользователем")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
