# client/client.py
import asyncio

from data_sync import DataSynchronizer
from gift_processor import GiftProcessor
from logger import logger
from shared_state import SharedState
from stream_monitor import StreamMonitor
from streamer_manager import StreamerManager
from TikTokLive.client.web.web_settings import WebDefaults


class TikTokMonitor:
    def __init__(self, db, api_key=None):
        # Инициализация общего состояния
        self.db = db
        self.api_key = api_key
        self.state = SharedState(db, api_key)

        # Инициализация компонентов
        self.gift_processor = GiftProcessor(db, self.state)
        self.data_sync = DataSynchronizer(db, self.state)
        self.stream_monitor = StreamMonitor(
            db, self.gift_processor, self.state, None
        )  # Временно None
        self.streamer_manager = StreamerManager(db, self.state, self.stream_monitor)

        # Устанавливаем связь stream_monitor с streamer_manager
        self.stream_monitor.streamer_manager = self.streamer_manager

        # Настройка API ключа для TikTokLive
        if api_key:
            WebDefaults.tiktok_sign_api_key = api_key
        else:
            logger.warning("No TikTokLive API key provided, connections may be limited")

    # Рабочая версия
    # async def start(self):
    #     """Запуск мониторинга"""
    #     # Запускаем обработку подарков
    #     gift_processor_task = asyncio.create_task(
    #         self.gift_processor._process_gift_queue()
    #     )

    #     # Запускаем обновление списка стримеров
    #     updater_task = asyncio.create_task(self.streamer_manager._update_streamers())

    #     # Запускаем очистку кэша подарков
    #     cleaner_task = asyncio.create_task(self.gift_processor._clean_gift_cache())

    #     # Запускаем регулярную синхронизацию
    #     sync_task = asyncio.create_task(self.data_sync._schedule_periodic_sync())

    #     # Ждем завершения всех задач
    #     await asyncio.gather(gift_processor_task, updater_task, cleaner_task, sync_task)

    async def start(self):
        """Запуск мониторинга"""
        self.tasks = []  # Очищаем список задач

        # Запускаем процессор подарков
        gift_tasks = await self.gift_processor.start()
        self.tasks.extend(gift_tasks)

        # Запускаем обновление списка стримеров
        updater_task = asyncio.create_task(self.streamer_manager._update_streamers())
        self.tasks.append(updater_task)

        # Запускаем регулярную синхронизацию
        sync_task = asyncio.create_task(self.data_sync._schedule_periodic_sync())
        self.tasks.append(sync_task)

        logger.info("TikTok monitoring started successfully")

        # Ожидаем завершения всех задач
        await asyncio.gather(*self.tasks)

    async def stop(self):
        """Остановка мониторинга"""
        logger.info("Shutting down parser...")

        # Устанавливаем флаг завершения
        self.state.shutdown_event.set()

        # Отменяем все задачи мониторинга
        for task in self.state.monitored_streams.values():
            task.cancel()

        # Ждем завершения обработки очереди подарков
        logger.info(
            f"Waiting for {self.gift_processor.gift_queue.qsize()} gifts to be processed"
        )

        # Ждем до 5 секунд для обработки оставшихся подарков
        try:
            for _ in range(50):  # 5 секунд (50 * 0.1)
                if self.gift_processor.gift_queue.empty():
                    break
                await asyncio.sleep(0.1)
        except Exception:
            pass

        logger.info("Monitor shutdown completed")

    # Проксируем методы из других классов для поддержания обратной совместимости
    async def sync_gift_streamers(self):
        return await self.data_sync.sync_gift_streamers()

    async def debug_tiktok_connection(self, username):
        return await self.streamer_manager.debug_tiktok_connection(username)
