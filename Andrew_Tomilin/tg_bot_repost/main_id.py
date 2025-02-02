import asyncio
import logging
import os
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

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

# 🔹 Удаляем стандартные обработчики Loguru (чтобы избежать дублирования)
logger.remove()

# 🔹 Логирование в файл
logger.add(
    "log_message.log",
    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль с цветами
logger.add(
    sys.stderr,
    format="<green>{time}</green> - <level>{level}</level> - <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)

# 🔹 Отключаем стандартное логирование SQLAlchemy
for handler in logging.getLogger("sqlalchemy.engine").handlers[:]:
    logging.getLogger("sqlalchemy.engine").removeHandler(handler)

logging.getLogger("sqlalchemy.engine").propagate = False


# 🔹 Перенаправляем логи SQLAlchemy в Loguru
class InterceptHandler(logging.Handler):
    def emit(self, record):
        level = record.levelname
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
sqlalchemy_logger.setLevel(logging.INFO)
sqlalchemy_logger.addHandler(InterceptHandler())

# 🔹 Проверка логов
logger.info("📌 Логирование SQLAlchemy перенаправлено в Loguru!")

load_dotenv(env_file_path)

# 🔹 Укажи данные из my.telegram.org
API_ID = 20270186  # Твой API ID
API_HASH = "1f58c726fd918821b4fb08a00e919b13"  # Твой API Hash
BOT_TOKEN_REPOST = os.getenv("BOT_TOKEN_REPOST")
SESSION_PATH = os.getenv("SESSION_PATH")
CHANNEL_ID_MATERIALS_PRO = int(os.getenv("CHANNEL_ID_MATERIALS_PRO"))
CHANNEL_ID_MATERIALS_FREE = int(os.getenv("CHANNEL_ID_MATERIALS_FREE"))
CHANNEL_ID_MODELS_PRO = int(os.getenv("CHANNEL_ID_MODELS_PRO"))
CHANNEL_ID_MODELS_FREE = int(os.getenv("CHANNEL_ID_MODELS_FREE"))
TIME_A = int(os.getenv("TIME_A"))
TIME_B = int(os.getenv("TIME_B"))

session_directory = current_directory / SESSION_PATH
session_directory.mkdir(parents=True, exist_ok=True)
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"sqlite+aiosqlite:///{os.path.abspath(DB_NAME)}"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


bot = Bot(token=BOT_TOKEN_REPOST)
dp = Dispatcher()


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


# async def fetch_pending_messages(limit: int = 10):
#     """Получает сообщения из БД, где repost=False"""
#     async with async_session() as session:
#         result = await session.execute(
#             select(RepostMessage).where(RepostMessage.repost == False).limit(limit)
#         )
#         messages = result.scalars().all()
#         return messages  # Возвращает список объектов RepostMessage


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
    logger.info(f"✅ Используется сессия: {session_name}")
    return phone_number, str(session_name)  # Преобразуем Path в строку


phone_number, session_name = get_session_name()  # Получаем номер телефона и имя сессии


async def fetch_and_save_messages():

    async with TelegramClient(session_name, API_ID, API_HASH) as client:
        await client.start(phone_number)

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


# # # Рабочий код пересылки сообщений
# async def get_and_forward_messages(limit: int = 10):
#     """Пересылает сообщения и обновляет статус в БД"""
#     messages = await fetch_pending_messages(limit)  # Загружаем сообщения

#     if not messages:
#         print("❌ Нет сообщений для пересылки.")
#         return

#     async with TelegramClient("session_name", API_ID, API_HASH) as client:
#         await client.start(PHONE_NUMBER)

#         try:
#             entity = await client.get_entity(CHANNEL_ID_MATERIALS_PRO)
#             print(f"✅ Канал найден: {entity.id}")
#         except ValueError as e:
#             print(f"❌ Ошибка: {e}")
#             return

#         success_ids = []

#         # 📌 Пересылаем сообщения
#         for msg in messages:
#             try:
#                 await client.forward_messages(
#                     CHANNEL_ID_MATERIALS_FREE,
#                     msg.message_id,
#                     from_peer=CHANNEL_ID_MATERIALS_PRO,
#                 )
#                 print(f"✅ Переслано сообщение {msg.message_id}")
#                 success_ids.append(msg.message_id)  # Сохраняем ID успешных пересылок
#             except Exception as e:
#                 print(f"❌ Ошибка при пересылке {msg.message_id}: {e}")

#         # 📌 Обновляем статус в БД
#         async with async_session() as session:
#             await session.execute(
#                 update(RepostMessage)
#                 .where(RepostMessage.message_id.in_(success_ids))
#                 .values(repost=True, reposted_at=datetime.now(timezone.utc))
#             )
#             await session.commit()

#         print(f"✅ Пересылка завершена! Всего переслано: {len(success_ids)} сообщений.")


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


# 🔹 Пересылка сообщений
async def get_and_forward_messages(category: str, limit: int):
    """Пересылает указанное количество сообщений."""
    message_ids = await fetch_pending_messages(category, limit)

    if not message_ids:
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
        await client.start(phone_number)
        success_ids = []
        for msg_id in message_ids:
            try:
                await client.forward_messages(
                    to_channel, msg_id, from_peer=from_channel
                )
                success_ids.append(msg_id)
                # 🔹 Добавляем случайную паузу
                delay = random.uniform(TIME_A, TIME_B)  # Генерируем случайную задержку
                logger.info(
                    f"⏳ Ожидание {delay:.2f} секунд перед следующим сообщением..."
                )
                await asyncio.sleep(delay)  # Асинхронная пауза
            except Exception as e:
                logger.error(f"❌ Ошибка при пересылке {msg_id}: {e}")

    if success_ids:
        await update_reposted_messages(success_ids)


async def main():
    logger.info("✅ Бот запущен!")
    await dp.start_polling(bot)  # Запускаем бота
    # try:
    #     logger.info("✅ Бот запущен!")
    #     await dp.start_polling(bot)  # Запускаем бота
    # except (KeyboardInterrupt, SystemExit):
    #     logger.warning("⏹ Бот остановлен пользователем!")
    # finally:
    #     logger.info("🛑 Завершение работы бота...")
    #     await bot.session.close()  # Корректно закрываем сессию бота
    #     logger.info("✅ Сессия бота закрыта.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
