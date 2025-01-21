import asyncio
import sys
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


async def send_to_api(data):
    """
    Отправляет данные на API, игнорируя проверку SSL.
    :param data: словарь с данными
    :return: ответ от API
    """
    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.post(API_URL, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Ошибка при отправке данных на API: {e}")
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


def get_session_name():
    """Получить имя сессии на основе ввода номера телефона."""
    phone_number = input("Введите номер телефона (в формате +1234567890): ").strip()
    session_name = session_directory / f"{phone_number}.session"
    return phone_number, session_name


async def send_message(client):
    """Отправка сообщения через Telegram и получение информации об участниках."""
    while True:
        try:
            target = input(
                "Введите ID или имя пользователя (например, @username): "
            ).strip()
            entity = await validate_target(client, target)
            if not entity:
                # Если цель не найдена, запрашиваем ввод @username
                target = input("Цель не найдена. Введите @username: ").strip()
                # Проверяем введенный @username
                entity = await validate_target(client, target)
                if not entity:
                    logger.error(
                        "Пользователь с данным @username не найден. Попробуйте снова."
                    )
                    continue  # Возвращаемся к началу цикла для нового ввода

            message = input("Введите текст сообщения: ").strip()

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
                "recipient_type": recipient_info["type"],
                "message": message,
            }

            # Отправляем данные на API и получаем ответ
            response_data = await send_to_api(all_data)

            if response_data:
                logger.info(f"Данные успешно отправлены: {response_data}")
                # print("\nДанные сообщения успешно отправлены")

            # Корректное завершение программы
            await client.disconnect()
            sys.exit(0)

        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            # Предлагаем пользователю ввести данные снова
            logger.info("Пожалуйста, попробуйте ввести данные снова.")


async def main():
    """Основная функция."""
    phone_number, session_name = get_session_name()
    client = TelegramClient(str(session_name), API_ID, API_HASH)

    await client.start(phone=phone_number)
    logger.info("Клиент запущен.")

    # В main теперь только отправка сообщения
    await send_message(client)


if __name__ == "__main__":
    asyncio.run(main())
