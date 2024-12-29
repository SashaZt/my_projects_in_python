from config.logger_setup import logger
from telethon import TelegramClient


async def send_message(client: TelegramClient, group_list: list, message: str):
    """
    Рассылает сообщение в указанные группы.
    """
    for group in group_list:
        try:
            await client.send_message(group, message)
            logger.info(f"Сообщение отправлено в {group}")
        except Exception as e:
            logger.error(f"Ошибка при отправке в {group}: {e}")
