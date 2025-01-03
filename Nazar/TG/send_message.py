from telethon import TelegramClient, events
from telethon.tl.functions.contacts import (  # Импорт для добавления контактов
    AddContactRequest,
)

# Укажите свои API ID и API Hash, которые вы можете получить на https://my.telegram.org
api_id = "20270186"
api_hash = "1f58c726fd918821b4fb08a00e919b13"

# Укажите имя сессии
session_name = "client_session"

# Создаем клиента
client = TelegramClient(session_name, api_id, api_hash)

# Словарь для хранения входящих сообщений, разделенных по пользователям/группам
incoming_messages = {}


@client.on(events.NewMessage)
async def handle_message(event):
    # Информация об отправителе
    sender = await event.get_sender()
    sender_name = sender.username or f"{sender.first_name} {sender.last_name}".strip()
    source = (
        f"{sender_name} ({sender.id})"
        if event.is_private
        else f"{event.chat.title} ({event.chat_id})"
    )

    # Информация о получателе (назначении)
    me = await client.get_me()
    destination = f"{me.first_name} {me.last_name or ''} (ID: {me.id})"

    # Сохраняем сообщение в словарь
    if source not in incoming_messages:
        incoming_messages[source] = []
    incoming_messages[source].append(event.text)

    # Выводим сообщение с источником и назначением
    print(f"Источник: {source}\nНазначение: {destination}\nСообщение: {event.text}\n")

    # Сохраняем в файл, если нужно
    with open("messages_log.txt", "a", encoding="utf-8") as file:
        file.write(
            f"Источник: {source}\nНазначение: {destination}\nСообщение: {event.text}\n\n"
        )


# Функция для отправки сообщения
async def send_message_to_user(user_id, message):
    try:
        # Отправляем сообщение пользователю
        await client.send_message(user_id, message)
        print(f"Сообщение отправлено пользователю с ID {user_id}: {message}")
    except Exception as e:
        print(f"Ошибка при отправке сообщения пользователю с ID {user_id}: {e}")


async def check_entity(target):
    try:
        entity = await client.get_entity(target)
        print(f"Найдено: {entity.id} ({entity.title or entity.username})")
    except Exception as e:
        print(f"Ошибка: {e}")


async def add_contact(phone, first_name, last_name=""):
    try:
        result = await client(
            AddContactRequest(phone=phone, first_name=first_name, last_name=last_name)
        )
        print("Пользователь добавлен в контакты.")
    except Exception as e:
        print(f"Ошибка при добавлении контакта: {e}")


# Запускаем клиента
async def main():
    print("Клиент запускается. Авторизуйтесь в Telegram...")
    await client.start()
    print("Клиент запущен. Ожидаем сообщения...")

    # Пример отправки сообщений через консоль
    while True:
        print("\nВыберите действие:")
        print("1. Отправить сообщение")
        print("2. Проверить сущность")
        print("3. Добавить контакт")
        print("4. Выйти")

        choice = input("Ваш выбор: ")
        if choice == "1":
            target = input("Введите ID или имя пользователя: ")
            message = input("Введите сообщение: ")
            await send_message_to_user(target, message)
        elif choice == "2":
            target = input("Введите ID или имя пользователя: ")
            await check_entity(target)
        elif choice == "3":
            phone = input("Введите номер телефона: ")
            first_name = input("Введите имя: ")
            last_name = input("Введите фамилию (опционально): ")
            await add_contact(phone, first_name, last_name)
        elif choice == "4":
            print("Выход...")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")

    await client.run_until_disconnected()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
