from config.config import API_HASH, API_ID, SESSION_NAME
from config.logger_setup import logger
from telethon import TelegramClient


async def authorize():
    """
    Авторизация пользователя и сохранение сессии.
    """
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        logger.info("Пользователь не авторизован. Запрашиваем код...")
        phone_number = input("Введите ваш номер телефона с кодом страны: ")
        await client.send_code_request(phone_number)
        code = input("Введите код из Telegram: ")
        await client.sign_in(phone_number, code)

    logger.info("Авторизация прошла успешно!")
    return client
