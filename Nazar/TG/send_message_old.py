# РАБОЧИЙ КОД
import asyncio
from pathlib import Path

import httpx
from configuration.config import API_HASH, API_ID, API_URL, SESSION_PATH
from configuration.logger_setup import logger
from telethon import TelegramClient, events
from telethon.errors import PeerIdInvalidError

# Указываем путь к папке для сессий
current_directory = Path.cwd()
session_directory = current_directory / SESSION_PATH
session_directory.mkdir(parents=True, exist_ok=True)


def get_session_name():
    """Получить имя сессии на основе ввода номера телефона."""
    phone_number = input("Введите номер телефона (в формате +1234567890): ").strip()
    session_name = session_directory / f"{phone_number}.session"
    return phone_number, session_name


async def get_user_info(client, user):
    """Получить информацию о пользователе в нужном формате."""
    try:
        full_user = await client.get_entity(user)
        name = f"{getattr(full_user, 'first_name', '') or ''} {getattr(full_user, 'last_name', '') or ''}".strip()
        username = getattr(full_user, "username", None)
        user_id = full_user.id
        phone = getattr(full_user, "phone", None)
        # Определяем тип пользователя
        user_type = "bot" if getattr(full_user, "bot", False) else "user"

        return {
            "name": name,
            "username": username,
            "id": user_id,
            "phone": phone,
            "type": user_type,
        }
    except Exception as e:
        logger.error(f"Ошибка при получении информации о пользователе: {e}")
        return None


async def validate_target(client, target):
    """Проверить, существует ли пользователь или группа."""
    try:
        if target.isdigit():
            entity = await client.get_entity(int(target))
        else:
            entity = await client.get_input_entity(target)
        logger.info(
            f"Цель найдена: {entity.id} ({entity.username or entity.first_name})"
        )
        return entity
    except PeerIdInvalidError:
        logger.error(f"Цель не найдена: {target}")
    except Exception as e:
        logger.error(f"Ошибка при проверке цели: {e}")
    return None


async def send_to_api(data):
    """
    Отправляет данные на API, игнорируя проверку SSL.
    :param data: словарь с данными
    """
    async with httpx.AsyncClient(verify=False) as client:  # Отключаем проверку SSL
        try:
            response = await client.post(API_URL, json=data)
            response.raise_for_status()  # Проверяем статус ответа
            logger.info(f"Данные успешно отправлены: {response.json()}")
        except httpx.HTTPError as e:
            logger.error(f"Ошибка при отправке данных на API: {e}")


async def send_message(client):
    """Отправка сообщения через Telegram и получение информации об участниках."""
    target = input("Введите ID или имя пользователя (например, @username): ").strip()
    entity = await validate_target(client, target)
    if not entity:
        logger.error("Цель не найдена. Завершение программы.")
        return

    message = input("Введите текст сообщения: ").strip()

    try:
        # Отправляем сообщение
        sent_message = await client.send_message(entity, message)

        # Получаем информацию об отправителе (текущем пользователе)
        sender_info = await get_user_info(client, "me")

        # Получаем информацию о получателе
        recipient_info = await get_user_info(client, entity)

        # Формируем данные в нужном формате
        all_data = {
            "sender_name": sender_info["name"],
            "sender_username": sender_info["username"],
            "sender_id": sender_info["id"],
            "sender_phone": sender_info["phone"],
            "sender_type": sender_info["type"],
            "recipient_name": recipient_info["name"],
            "recipient_username": recipient_info["username"],
            "recipient_id": recipient_info["id"],
            "recipient_phone": recipient_info["phone"],
            # "recipient_type": recipient_info["type"],
            "message": message,
        }

        # Отправляем данные на API
        await send_to_api(all_data)

        # logger.info(f"Данные сообщения: {all_data}")
        # print("\nДанные сообщения:")
        # for key, value in all_data.items():
        #     print(f"{key}: {value}")

    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")


async def handle_message(event, client):
    """Обработка входящего сообщения."""
    try:
        # Получаем информацию об отправителе
        sender_info = await get_user_info(client, await event.get_sender())

        # Получаем информацию о получателе (текущем пользователе)
        recipient_info = await get_user_info(client, "me")

        # Формируем данные в нужном формате
        all_data = {
            "sender_name": sender_info["name"],
            "sender_username": sender_info["username"],
            "sender_id": sender_info["id"],
            "sender_phone": sender_info["phone"],
            "sender_type": sender_info["type"],
            "recipient_name": recipient_info["name"],
            "recipient_username": recipient_info["username"],
            "recipient_id": recipient_info["id"],
            "recipient_phone": recipient_info["phone"],
            # "recipient_type": recipient_info["type"],
            "message": event.text,
        }

        # Отправляем данные на API
        await send_to_api(all_data)

    except Exception as e:
        logger.error(f"Ошибка при обработке входящего сообщения: {e}")


async def main():
    """Основная функция."""
    phone_number, session_name = get_session_name()
    client = TelegramClient(str(session_name), API_ID, API_HASH)

    await client.start(phone=phone_number)
    logger.info("Клиент запущен.")

    # Регистрируем обработчик событий
    @client.on(events.NewMessage)
    async def message_handler(event):
        await handle_message(event, client)

    # Параллельно выполняем отправку сообщения и обработку событий
    await asyncio.gather(
        send_message(client),
        client.run_until_disconnected(),
    )


if __name__ == "__main__":
    asyncio.run(main())
