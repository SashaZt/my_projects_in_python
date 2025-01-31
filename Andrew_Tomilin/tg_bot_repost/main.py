import asyncio
import os
from datetime import datetime  # Нужно добавить этот импорт
from datetime import timezone  # Добавляем импорт timezone

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage  # Добавляем импорт
from aiogram.types import BotCommand, CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from configuration.logger_setup import logger
from dotenv import load_dotenv
from sqlalchemy import DateTime  # И этот тоже для колонки created_at
from sqlalchemy import (  # Добавляем импорт func
    Boolean,
    Column,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    select,
    update,
)
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)
# 🔹 Настройки бота и каналов
CHANNEL_ID_MODELS_PRO = int(os.getenv("CHANNEL_ID_MODELS_PRO"))  # Преобразуем в int
CHANNEL_ID_MODELS_FREE = int(os.getenv("CHANNEL_ID_MODELS_FREE"))
CHANNEL_ID_MATERIALS_PRO = int(os.getenv("CHANNEL_ID_MATERIALS_PRO"))
CHANNEL_ID_MATERIALS_FREE = int(os.getenv("CHANNEL_ID_MATERIALS_FREE"))
BOT_TOKEN_REPOST = os.getenv("BOT_TOKEN_REPOST")

DB_NAME = os.getenv("DB_NAME")
TABLE_NAME = os.getenv("TABLE_NAME")
TIME_A = int(os.getenv("TIME_A", 5))
TIME_B = int(os.getenv("TIME_B", 10))

# Добавим проверку
if not all(
    [
        CHANNEL_ID_MODELS_PRO,
        CHANNEL_ID_MODELS_FREE,
        CHANNEL_ID_MATERIALS_PRO,
        CHANNEL_ID_MATERIALS_FREE,
    ]
):
    raise ValueError("Один или несколько ID каналов не установлены в .env файле")

bot = Bot(token=BOT_TOKEN_REPOST)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)
# 🔹 Настройки БД (асинхронный SQLite)
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.abspath(DB_NAME)}"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# Создаем класс состояний
class RepostStates(StatesGroup):
    waiting_count_models = State()
    waiting_count_materials = State()


# 🔹 Модель базы данных
class Base(DeclarativeBase):
    pass


class RepostMessage(Base):
    __tablename__ = TABLE_NAME

    __table_args__ = (
        Index("idx_category_repost", "category", "repost"),
        # Составной уникальный индекс
        UniqueConstraint("message_id", "category", name="uix_message_category"),
    )

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, nullable=False)  # Убрали unique=True
    category = Column(String, nullable=False)
    repost = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reposted_at = Column(DateTime, nullable=True)


# Создаем клавиатуру с выбором действий
def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Models Pro → Free", callback_data="repost_models")
    )
    builder.add(
        InlineKeyboardButton(
            text="Materials Pro → Free", callback_data="repost_materials"
        )
    )
    return builder.as_markup()


async def set_commands():
    commands = [
        BotCommand(command="menu", description="Открыть меню пересылки"),
        BotCommand(command="cancel", description="Отменить текущую операцию"),
        BotCommand(command="send_all", description="Переслать все новые сообщения"),
    ]
    await bot.set_my_commands(commands)


# Команда для показа меню
@dp.message(Command("menu"))
async def show_menu(message: Message):
    await message.answer(
        "Выберите тип контента для пересылки:", reply_markup=get_main_keyboard()
    )


# Обработчик нажатий на кнопки
@dp.callback_query(F.data.startswith("repost_"))
async def handle_repost(callback: CallbackQuery, state: FSMContext):
    category = callback.data.replace("repost_", "")

    if category == "models":
        await state.set_state(RepostStates.waiting_count_models)
    else:
        await state.set_state(RepostStates.waiting_count_materials)

    await callback.message.answer(
        f"Укажите количество сообщений для пересылки из {category.title()}:"
    )
    await callback.answer()


# Обработчик ответа с количеством
@dp.message(lambda message: message.text.isdigit())
async def process_count(message: Message, state: FSMContext):
    count = int(message.text)
    if count <= 0:
        await message.answer("Количество должно быть больше 0")
        return
    if count > 100:  # Ограничение на количество
        await message.answer("Максимальное количество для пересылки - 100 сообщений")
        return

    current_state = await state.get_state()

    if current_state == RepostStates.waiting_count_models:
        category = "models"
        from_chat = CHANNEL_ID_MODELS_PRO
        to_chat = CHANNEL_ID_MODELS_FREE
    elif current_state == RepostStates.waiting_count_materials:
        category = "materials"
        from_chat = CHANNEL_ID_MATERIALS_PRO
        to_chat = CHANNEL_ID_MATERIALS_FREE
    else:
        return

    # # Получаем параметры для пересылки
    # if category == "models":
    #     from_chat = CHANNEL_ID_MODELS_PRO
    #     to_chat = CHANNEL_ID_MODELS_FREE
    # else:
    #     from_chat = CHANNEL_ID_MATERIALS_PRO
    #     to_chat = CHANNEL_ID_MATERIALS_FREE

    # Получаем сообщения для пересылки
    async with SessionLocal() as session:
        query = (
            select(RepostMessage)
            .where(RepostMessage.category == category, RepostMessage.repost == False)
            .order_by(RepostMessage.message_id.asc())
            .limit(count)
        )

        messages = (await session.execute(query)).scalars().all()

        if not messages:
            await message.answer(
                f"Нет новых сообщений для пересылки в категории {category}"
            )
            await state.clear()
            return

        success_count = 0
        for msg in messages:
            try:
                await bot.forward_message(
                    chat_id=to_chat, from_chat_id=from_chat, message_id=msg.message_id
                )

                # Обновляем статус
                msg.repost = True
                msg.reposted_at = datetime.now(timezone.utc)
                success_count += 1

                if success_count % 10 == 0:
                    await message.answer(
                        f"Переслано {success_count} из {len(messages)}"
                    )

            except Exception as e:
                logger.error(f"Ошибка при пересылке сообщения {msg.message_id}: {e}")

        await session.commit()

        # Отправляем итоговый отчет
        await message.answer(
            f"Пересылка завершена!\n"
            f"Успешно переслано: {success_count} из {len(messages)}"
        )

    await state.clear()


# 🔹 Создание таблицы (при первом запуске)
async def init_db():

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# 🔹 Получаем ID всех сообщений из группы
async def fetch_all_messages(chat_id: int, category: str):
    async with SessionLocal() as session:
        try:
            # Проверяем текущее состояние
            min_id, max_id, total_count = await check_database_state(category)

            # Получаем последнее сообщение в канале
            last_message = await bot.send_message(chat_id=chat_id, text=".")
            last_message_id = last_message.message_id
            await bot.delete_message(chat_id=chat_id, message_id=last_message_id)

            if max_id and max_id >= last_message_id:
                logger.info(f"Нет новых сообщений для категории {category}")
                return

            # Добавляем только новые сообщения
            start_id = (max_id or 0) + 1
            new_messages = []

            for msg_id in range(start_id, last_message_id + 1):
                new_messages.append(
                    {
                        "message_id": msg_id,
                        "category": category,
                        "created_at": datetime.now(timezone.utc),
                        "repost": False,
                    }
                )

                if len(new_messages) >= 100:
                    await session.execute(
                        RepostMessage.__table__.insert(), new_messages
                    )
                    await session.commit()
                    logger.info(f"Добавлено {len(new_messages)} новых сообщений")
                    new_messages = []

            if new_messages:
                await session.execute(RepostMessage.__table__.insert(), new_messages)
                await session.commit()
                logger.info(f"Добавлено {len(new_messages)} новых сообщений")

            # Проверяем финальное состояние
            await check_database_state(category)

        except Exception as e:
            logger.error(f"Ошибка при получении сообщений: {e}")
            await session.rollback()
            raise


# 🔹 Фиксируем новые сообщения при старте бота
async def sync_messages():
    try:
        # await clean_and_fetch_messages(CHANNEL_ID_MODELS_PRO, "models")
        await fetch_all_messages(CHANNEL_ID_MODELS_PRO, "models")
        await fetch_all_messages(CHANNEL_ID_MATERIALS_PRO, "materials")
    except Exception as e:
        logger.error(f"Ошибка при синхронизации сообщений: {e}")
        raise


# 🔹 Фиксируем новые сообщения при старте бота
async def send_batch(category: str, from_chat: int, to_chat: int):
    async with SessionLocal() as session:
        result = await session.execute(
            select(RepostMessage)
            .where(RepostMessage.category == category, RepostMessage.repost == False)
            .limit(100)
        )
        messages = result.scalars().all()

        if not messages:
            return f"✅ Все {category} сообщения уже пересланы!"

        try:
            message_ids = [msg.message_id for msg in messages]
            await bot.copy_messages(
                chat_id=to_chat, from_chat_id=from_chat, message_ids=message_ids
            )

            # Обновляем статус пересылки
            for msg in messages:
                await session.execute(
                    update(RepostMessage)
                    .where(RepostMessage.message_id == msg.message_id)
                    .values(repost=True, reposted_at=datetime.now(timezone.utc))
                )
            await session.commit()

            return f"📨 Переслано {len(messages)} сообщений из {category}!"

        except Exception as e:
            logger.error(f"⚠ Ошибка пересылки для категории {category}: {e}")
            await session.rollback()
            return f"❌ Ошибка при пересылке сообщений {category}: {str(e)}"


# 🔹 Команда для старта рассылки
@dp.message(Command("send_all"))
async def send_all_messages(message: Message):
    result_models = await send_batch(
        "models", CHANNEL_ID_MODELS_PRO, CHANNEL_ID_MODELS_FREE
    )
    result_materials = await send_batch(
        "materials", CHANNEL_ID_MATERIALS_PRO, CHANNEL_ID_MATERIALS_FREE
    )

    await message.answer(f"{result_models}\n{result_materials}")


@dp.message(Command("cancel"))
@dp.message(F.text.lower() == "отмена")
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("Операция отменена.")


async def check_database_state(category: str):
    async with SessionLocal() as session:
        # Получаем максимальный и минимальный ID
        min_id = await session.scalar(
            select(RepostMessage.message_id)
            .where(RepostMessage.category == category)
            .order_by(RepostMessage.message_id.asc())
            .limit(1)
        )

        max_id = await session.scalar(
            select(RepostMessage.message_id)
            .where(RepostMessage.category == category)
            .order_by(RepostMessage.message_id.desc())
            .limit(1)
        )

        # Считаем общее количество записей
        total_count = await session.scalar(
            select(func.count(RepostMessage.id)).where(
                RepostMessage.category == category
            )
        )

        logger.info(
            f"Состояние БД для категории {category}:\n"
            f"Минимальный ID: {min_id}\n"
            f"Максимальный ID: {max_id}\n"
            f"Всего записей: {total_count}"
        )

        return min_id, max_id, total_count


# async def clean_and_fetch_messages(chat_id: int, category: str):
#     async with SessionLocal() as session:
#         try:
#             # Удаляем все записи для данной категории
#             await session.execute(
#                 delete(RepostMessage).where(RepostMessage.category == category)
#             )
#             await session.commit()
#             logger.info(f"Удалены все записи для категории {category}")

#             # Получаем последнее сообщение в канале
#             last_message = await bot.send_message(chat_id=chat_id, text=".")
#             last_message_id = last_message.message_id
#             await bot.delete_message(chat_id=chat_id, message_id=last_message_id)

#             # Добавляем новые сообщения
#             total_saved = 0
#             batch = []

#             for msg_id in range(1, last_message_id + 1):
#                 batch.append(
#                     {
#                         "message_id": msg_id,
#                         "category": category,
#                         "created_at": datetime.now(timezone.utc),
#                         "repost": False,
#                     }
#                 )

#                 if len(batch) >= 100:
#                     await session.execute(RepostMessage.__table__.insert(), batch)
#                     await session.commit()
#                     total_saved += len(batch)
#                     logger.info(f"Сохранено {total_saved} сообщений для {category}")
#                     batch = []

#             # Сохраняем оставшиеся
#             if batch:
#                 await session.execute(RepostMessage.__table__.insert(), batch)
#                 await session.commit()
#                 total_saved += len(batch)

#             logger.info(
#                 f"Завершено сохранение {total_saved} сообщений для категории {category}. "
#                 f"Диапазон ID: 1 - {last_message_id}"
#             )

#         except Exception as e:
#             logger.error(f"Ошибка: {e}")
#             await session.rollback()
#             raise


async def on_shutdown():
    logger.info("Shutting down...")
    await bot.session.close()


async def main():
    logger.info("Starting bot...")
    logger.info(f"Models Pro Channel ID: {CHANNEL_ID_MODELS_PRO}")
    logger.info(f"Models Free Channel ID: {CHANNEL_ID_MODELS_FREE}")
    logger.info(f"Materials Pro Channel ID: {CHANNEL_ID_MATERIALS_PRO}")
    logger.info(f"Materials Free Channel ID: {CHANNEL_ID_MATERIALS_FREE}")

    try:
        await init_db()
        await set_commands()  # Добавляем эту строку
        await sync_messages()
        logger.info("Bot is ready to work!")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка в main: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped due to error: {e}")
    finally:
        asyncio.run(on_shutdown())
