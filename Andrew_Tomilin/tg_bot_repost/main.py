import asyncio
import os
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite
from aiogram import F  # ✅ Правильный импорт для callback_data
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
    select,
    text,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from telethon.sync import TelegramClient

current_directory = Path.cwd()
configuration_directory = current_directory / "configuration"
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"
env_file_path = configuration_directory / ".env"
load_dotenv(env_file_path)
# 🔹 Укажи данные из my.telegram.org
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN_REPOST = os.getenv("BOT_TOKEN_REPOST")
SESSION_PATH = os.getenv("SESSION_PATH")
CHANNEL_ID_MATERIALS_PRO = int(os.getenv("CHANNEL_ID_MATERIALS_PRO"))
CHANNEL_ID_MATERIALS_FREE = int(os.getenv("CHANNEL_ID_MATERIALS_FREE"))
CHANNEL_ID_MODELS_PRO = int(os.getenv("CHANNEL_ID_MODELS_PRO"))
CHANNEL_ID_MODELS_FREE = int(os.getenv("CHANNEL_ID_MODELS_FREE"))
TIME_A = int(os.getenv("TIME_A"))
TIME_B = int(os.getenv("TIME_B"))
# password = os.getenv("TELEGRAM_PASSWORD")
session_directory = current_directory / SESSION_PATH
session_directory.mkdir(parents=True, exist_ok=True)
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"sqlite+aiosqlite:///{os.path.abspath(DB_NAME)}"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


bot = Bot(token=BOT_TOKEN_REPOST)
dp = Dispatcher()
## 🔹 Удаляем все стандартные обработчики Loguru (избегаем дублирования)
logger.remove()

# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


# 🔹 Определение базы данных
class Base(DeclarativeBase):
    pass


class RepostMessage(Base):
    __tablename__ = "repost_messages"

    __table_args__ = (
        Index("idx_category_repost", "category", "repost"),
        UniqueConstraint("message_id", "category", name="uix_message_category"),
    )

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    repost = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reposted_at = Column(DateTime, nullable=True)


# 🔹 Создание таблицы (при первом запуске)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def validate_phone_number(phone_number: str) -> str:
    """Проверяет корректность номера телефона."""
    if not re.match(r"^\+\d{10,15}$", phone_number):
        raise ValueError("❌ Номер телефона должен быть в формате +1234567890.")
    return phone_number


def get_session_name():
    """Получает имя сессии: выбираем существующую или вводим новый номер."""
    sessions = list(session_directory.glob("*.session"))

    if sessions:
        logger.info("📌 Доступные сессии:")
        for i, session in enumerate(sessions, 1):
            logger.info(f"{i}. {session.stem}")

        choice = input(
            " Выберите номер сессии или введите новый номер телефона: "
        ).strip()

        try:
            # Если введено число, выбираем существующую сессию
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(sessions):
                phone_number = sessions[choice_idx].stem
            else:
                phone_number = input(
                    "📞 Введите новый номер телефона (в формате +1234567890): "
                ).strip()
                phone_number = validate_phone_number(phone_number)
        except ValueError:
            # Если ввели не число, проверяем номер телефона
            phone_number = validate_phone_number(choice)
    else:
        logger.error("\n❌ Нет сохраненных сессий.")
        phone_number = input(
            "📞 Введите номер телефона (в формате +1234567890): "
        ).strip()
        phone_number = validate_phone_number(phone_number)

    session_name = session_directory / f"{phone_number}.session"
    # Берем пароль из переменной окружения. Если пароль не установлен, можно запросить его:
    password = os.getenv("TELEGRAM_PASSWORD")
    if not password:
        logger.warning(
            "Пароль не задан в переменной окружения TELEGRAM_PASSWORD. Введите пароль вручную:"
        )
        password = input("Введите пароль: ").strip()
    logger.info(f"✅ Используется сессия: {session_name}")
    return phone_number, str(session_name), password  # Преобразуем Path в строку


phone_number, session_name, password = (
    get_session_name()
)  # Получаем номер телефона и имя сессии


async def fetch_and_save_messages():

    async with TelegramClient(session_name, API_ID, API_HASH) as client:
        await client.start(phone=phone_number, password=password)

        async with async_session() as session:
            batch_size = 500  # Количество сообщений на одну вставку
            categories = [
                ("materials_pro", CHANNEL_ID_MATERIALS_PRO),
                ("models_pro", CHANNEL_ID_MODELS_PRO),
            ]

            for category, channel_id in categories:
                # 🔹 1. Получаем последнее сообщение в БД
                result = await session.execute(
                    text(
                        "SELECT MAX(message_id) FROM repost_messages WHERE category = :category"
                    ),
                    {"category": category},
                )
                last_message_id = (
                    result.scalar() or 0
                )  # Если в БД нет сообщений, начинаем с 0

                logger.info(
                    f"📌 Последнее сообщение в БД для {category}: {last_message_id}"
                )

                entity = await client.get_entity(channel_id)
                logger.info(f"✅ Канал найден: {entity.id} ({category})")

                messages_to_insert = []

                # 🔹 2. Загружаем только новые сообщения
                async for message in client.iter_messages(
                    entity, reverse=True, min_id=last_message_id, limit=50000
                ):
                    messages_to_insert.append(
                        {
                            "message_id": message.id,
                            "category": category,
                            "repost": False,
                            "created_at": datetime.now(timezone.utc),
                        }
                    )

                    if len(messages_to_insert) >= batch_size:
                        await session.execute(
                            text(
                                """
                                INSERT INTO repost_messages (message_id, category, repost, created_at)
                                VALUES (:message_id, :category, :repost, :created_at)
                                ON CONFLICT(message_id, category) DO NOTHING
                                """
                            ),
                            messages_to_insert,
                        )
                        await session.commit()
                        logger.info(
                            f"✅ {batch_size} новых сообщений записано ({category})..."
                        )
                        messages_to_insert = []

                if messages_to_insert:
                    await session.execute(
                        text(
                            """
                            INSERT INTO repost_messages (message_id, category, repost, created_at)
                            VALUES (:message_id, :category, :repost, :created_at)
                            ON CONFLICT(message_id, category) DO NOTHING
                            """
                        ),
                        messages_to_insert,
                    )
                    await session.commit()
                    logger.info(
                        f"✅ Последние {len(messages_to_insert)} новых сообщений записано ({category})..."
                    )

            logger.info("✅ Все новые сообщения успешно записаны в базу данных")


# 🔹 Главное меню
async def main_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📩 Переслать Materials Pro → Free",
                    callback_data="send_materials",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📩 Переслать Models Pro → Free", callback_data="send_models"
                )
            ],
        ]
    )
    return keyboard


# 🔹 Обработчик команды /start
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("⏳ Обновляем список сообщений...")

    await fetch_and_save_messages()  # Обновляем список ID

    keyboard = await main_menu()
    await message.answer(
        "✅ Данные обновлены! Выберите действие:", reply_markup=keyboard
    )


# 🔹 Запрос количества сообщений перед пересылкой
@dp.callback_query(F.data.in_(["send_materials", "send_models"]))
async def ask_for_limit(callback_query: CallbackQuery):
    """Запрашивает у пользователя количество сообщений для пересылки."""
    await callback_query.answer()
    category = (
        "materials_pro" if callback_query.data == "send_materials" else "models_pro"
    )

    # Сохраняем категорию в `callback_query.message`
    await callback_query.message.answer(
        f"📩 Сколько сообщений переслать из {category.replace('_', ' ')}? (Введите число)"
    )

    # Устанавливаем состояние ожидания ввода
    dp.callback_query_data = {"category": category}


# 🔹 Обработчик ввода количества сообщений
@dp.message(F.text.regexp(r"^\d+$"))  # Разрешаем ввод только чисел
async def process_limit_input(message: types.Message):
    """Принимает число от пользователя и запускает пересылку сообщений."""
    limit = int(message.text)

    if limit <= 0:
        await message.answer("❌ Введите число больше 0.")
        return

    category = dp.callback_query_data.get(
        "category", "materials_pro"
    )  # Получаем сохранённую категорию
    await message.answer(
        f"⏳ Начинаем пересылку {limit} сообщений из {category.replace('_', ' ')}..."
    )

    # Запускаем пересылку сообщений с указанным количеством
    await get_and_forward_messages(category, limit)

    await message.answer(f"✅ Переслано {limit} сообщений!")


# 🔹 Функция получения сообщений из БД
async def fetch_pending_messages(category: str, limit: int = 10):
    async with async_session() as session:
        result = await session.execute(
            select(RepostMessage.message_id)
            .where(RepostMessage.category == category, RepostMessage.repost == False)
            .limit(limit)
        )
        return result.scalars().all()


# 🔹 Обновление статуса сообщений в БД
async def update_reposted_messages(message_ids):
    async with async_session() as session:
        await session.execute(
            update(RepostMessage)
            .where(RepostMessage.message_id.in_(message_ids))
            .values(repost=True, reposted_at=datetime.now(timezone.utc))
        )
        await session.commit()


# Рабочий код
# # 🔹 Пересылка сообщений
# async def get_and_forward_messages(category: str, limit: int):
#     """Пересылает указанное количество сообщений."""
#     message_ids = await fetch_pending_messages(category, limit)

#     if not message_ids:
#         return

#     to_channel = (
#         CHANNEL_ID_MATERIALS_FREE
#         if category == "materials_pro"
#         else CHANNEL_ID_MODELS_FREE
#     )
#     from_channel = (
#         CHANNEL_ID_MATERIALS_PRO
#         if category == "materials_pro"
#         else CHANNEL_ID_MODELS_PRO
#     )
#     async with TelegramClient(session_name, API_ID, API_HASH) as client:
#         await client.start(phone=phone_number, password=password)
#         success_ids = []
#         for msg_id in message_ids:
#             try:
#                 await client.forward_messages(
#                     to_channel, msg_id, from_peer=from_channel
#                 )
#                 success_ids.append(msg_id)
#                 # 🔹 Добавляем случайную паузу
#                 delay = random.uniform(TIME_A, TIME_B)  # Генерируем случайную задержку
#                 logger.info(
#                     f"⏳ Ожидание {delay:.2f} секунд перед следующим сообщением..."
#                 )
#                 await asyncio.sleep(delay)  # Асинхронная пауза
#             except Exception as e:
#                 logger.error(f"❌ Ошибка при пересылке {msg_id}: {e}")


#     if success_ids:
#         await update_reposted_messages(success_ids)
async def get_and_forward_messages(category: str, limit: int):
    """Пересылает сообщения парами (фото + архив) с паузой после каждой пары."""
    message_ids = await fetch_pending_messages(category, limit)

    if not message_ids:
        logger.info("📭 Нет сообщений для пересылки")
        return

    to_channel = (
        CHANNEL_ID_MATERIALS_FREE
        if category == "materials_pro"
        else CHANNEL_ID_MODELS_FREE
    )
    from_channel = (
        CHANNEL_ID_MATERIALS_PRO
        if category == "materials_pro"
        else CHANNEL_ID_MODELS_PRO
    )

    async with TelegramClient(session_name, API_ID, API_HASH) as client:
        await client.start(phone=phone_number, password=password)

        # Получаем сообщения
        messages = await client.get_messages(from_channel, ids=message_ids)

        # Фильтруем и разделяем по типам
        photo_messages = []
        archive_messages = []
        for msg in messages:
            if msg is None:
                logger.warning(
                    f"⚠️ Сообщение с ID из {message_ids} не найдено (возможно, удалено)"
                )
                continue
            if hasattr(msg, "photo") and msg.photo:
                photo_messages.append(msg)
            elif hasattr(msg, "document") and msg.document:
                archive_messages.append(msg)
            else:
                logger.info(
                    f"ℹ️ Сообщение с ID {msg.id} не является фото или архивом, пропускаем"
                )

        if not photo_messages or not archive_messages:
            logger.info(
                f"📉 Недостаточно фото ({len(photo_messages)}) или архивов ({len(archive_messages)}) для парного пересыла"
            )
            return

        success_ids = []
        pair_count = 0

        # Пересылаем парами
        for photo, archive in zip(photo_messages, archive_messages):
            try:
                # Фото
                await client.forward_messages(
                    to_channel, photo.id, from_peer=from_channel
                )
                success_ids.append(photo.id)
                logger.info(f"✅ Переслано фото с ID {photo.id}")

                # Архив
                await client.forward_messages(
                    to_channel, archive.id, from_peer=from_channel
                )
                success_ids.append(archive.id)
                logger.info(f"✅ Переслано архив с ID {archive.id}")

                pair_count += 1

                # Пауза после пары
                delay = random.uniform(TIME_A, TIME_B)
                logger.info(f"⏳ Ожидание {delay:.2f} секунд после пары...")
                await asyncio.sleep(delay)

                # Запись в БД после 50 пар
                if pair_count >= 15:
                    await update_reposted_messages(success_ids)
                    logger.info(f"📝 Записано {len(success_ids)} ID в базу данных")
                    success_ids = []
                    pair_count = 0

            except Exception as e:
                logger.error(
                    f"❌ Ошибка при пересылке пары (фото {photo.id}, архив {archive.id}): {e}"
                )

        # Записываем остатки
        if success_ids:
            await update_reposted_messages(success_ids)
            logger.info(f"📝 Записано оставшихся {len(success_ids)} ID в базу данных")


async def main():
    logger.info("✅ Бот запущен!")
    await dp.start_polling(bot)  # Запускаем бота


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
