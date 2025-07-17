import asyncio
import shutil
import signal
import time
import pandas as pd
from create_xml import export_products_to_xml
from downloader import downloader
from get_xml import parse_start_xml
from scrap import scrap_html_file, scrap_html_file_multithreaded

from config import Config, logger, paths

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    logger.info(f"Получен сигнал {signum}, завершение работы...")
    sys.exit(0)


async def main():
    output_csv_file = paths.data / "output.csv"
    df = pd.read_csv(output_csv_file, encoding="utf-8")
    urls = df["url"].tolist()
    # Скачиваем
    results = await downloader.download_urls(urls)
    logger.info("🎯 Результаты:")
    for url, success in results.items():
        status = "✅ Успешно" if success else "❌ Ошибка"
        logger.info(f"{status}: {url}")

    # Статистика
    logger.info(f"\n📊 Финальная статистика: {downloader.get_stats()}")


if __name__ == "__main__":
    # Регистрируем обработчики сигналов
    # signal.signal(signal.SIGTERM, signal_handler)
    # signal.signal(signal.SIGINT, signal_handler)
    #  # Явное завершение
    if paths.temp.exists():
        shutil.rmtree(paths.temp)
        paths.create_directories()
    parse_start_xml()
    asyncio.run(main())
    
    scrap_html_file_multithreaded()
    
    export_products_to_xml()

