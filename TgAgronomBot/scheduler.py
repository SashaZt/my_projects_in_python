import asyncio
import schedule
from send_messages_asio import send_messages_to_traders
from trial_end_messages import check_and_send_trial_end_messages
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_schedule():
    while True:
        # logger.info("Запуск задач schedule")
        schedule.run_pending()
        await asyncio.sleep(1)


def main():
    logger.info("Настройка schedule задач")
    # Используем schedule для планирования задач
    schedule.every(30).seconds.do(
        lambda: asyncio.create_task(send_messages_to_traders())
    )
    # schedule.every().day.at("08:00").do(
    #     lambda: asyncio.create_task(check_and_send_trial_end_messages())
    # )
    # schedule.every().day.at("12:00").do(
    #     lambda: asyncio.create_task(check_and_send_trial_end_messages())
    # )
    # schedule.every().day.at("16:00").do(
    #     lambda: asyncio.create_task(check_and_send_trial_end_messages())
    # )
    # Проверки каждые 5 минут для теста
    schedule.every(1).minutes.do(
        lambda: asyncio.create_task(check_and_send_trial_end_messages())
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_schedule())


if __name__ == "__main__":
    main()
