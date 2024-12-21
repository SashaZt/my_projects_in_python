import csv

from telethon.sync import TelegramClient
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import InputPeerEmpty

# Укажите ваши данные Telegram API
API_ID = "8771905"
API_HASH = "39debb7f571db5ad62288c20780af81c"

# Имя файла сессии
SESSION_NAME = "search_bot"

# Ключевые слова для поиска
KEYWORDS = ["грузоперевозки", "транспорт", "логистика", "перевозки"]

# Создание клиента с сохранением сессии
with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
    print("Сессия загружена или создана успешно.")

    # Открываем файл для записи результатов
    with open("groups.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Название", "ID", "Ссылка"])  # Заголовок CSV-файла

        # Поиск групп по ключевым словам
        for keyword in KEYWORDS:
            print(f"Поиск групп по ключевому слову: {keyword}")
            results = client(
                SearchRequest(
                    q=keyword,  # Поисковый запрос
                    limit=50,  # Максимальное количество результатов
                    filter=InputPeerEmpty(),
                )
            )

            # Обработка найденных групп
            for chat in results.chats:
                if chat.megagroup:  # Проверка, что это супергруппа
                    print(f"Группа: {chat.title}")
                    print(f"ID: {chat.id}")
                    print(
                        f"Ссылка: https://t.me/{chat.username if chat.username else 'invite-only'}"
                    )
                    writer.writerow(
                        [
                            chat.title,
                            chat.id,
                            f"https://t.me/{chat.username if chat.username else 'invite-only'}",
                        ]
                    )
