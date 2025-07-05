#!/usr/bin/env python3
"""
TikLeap Orchestrator - управляет полным циклом: авторизация -> сбор данных
Интегрируется с существующим tikleap_manager.sh
"""

import asyncio
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from loguru import logger

# Настройка логирования
logger.remove()
logger.add(
    "logs/orchestrator.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO",
    rotation="10 MB",
    retention="7 days",
)
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>",
    level="INFO",
)


class TikLeapOrchestrator:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.tikleap_manager = self.project_root / "tikleap_manager.sh"
        self.client_script = self.project_root / "client" / "main.py"
        self.cookies_file = self.project_root / "cookies" / "cookies_important.json"
        self.cookies_dir = self.project_root / "cookies"

        # Создаем директории если их нет
        self.cookies_dir.mkdir(exist_ok=True)
        (self.project_root / "logs").mkdir(exist_ok=True)

        logger.info(f"📁 Рабочая директория: {self.project_root}")
        logger.info(f"🔧 TikLeap manager: {self.tikleap_manager}")
        logger.info(f"📊 Client script: {self.client_script}")
        logger.info(f"🍪 Cookies file: {self.cookies_file}")

    def check_tikleap_manager(self):
        """Проверяет наличие tikleap_manager.sh"""
        if not self.tikleap_manager.exists():
            logger.error(f"❌ tikleap_manager.sh не найден: {self.tikleap_manager}")
            return False

        # Проверяем права на выполнение
        if not os.access(self.tikleap_manager, os.X_OK):
            logger.warning("⚠️ tikleap_manager.sh не имеет прав на выполнение")
            try:
                os.chmod(self.tikleap_manager, 0o755)
                logger.info("✅ Добавили права на выполнение")
            except Exception as e:
                logger.error(f"❌ Не удалось добавить права: {e}")
                return False

        return True

    def run_auth_via_manager(self):
        """Запускает авторизацию через tikleap_manager.sh --full"""
        try:
            if not self.check_tikleap_manager():
                return False

            logger.info("🔐 Запускаем процесс авторизации через tikleap_manager.sh...")

            # Удаляем старые cookies если есть
            if self.cookies_file.exists():
                self.cookies_file.unlink()
                logger.info("🗑️ Удалили старые cookies")

            # Удаляем все cookies файлы
            existing_cookies = list(self.cookies_dir.glob("*.json"))
            if existing_cookies:
                for cookie_file in existing_cookies:
                    cookie_file.unlink()
                    logger.info(f"🗑️ Удалили старый файл: {cookie_file.name}")

            # Запускаем tikleap_manager.sh --full
            logger.info(f"🚀 Выполняем: {self.tikleap_manager} --full")

            process = subprocess.Popen(
                [str(self.tikleap_manager), "--full"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_root),
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Читаем вывод в реальном времени
            logger.info("📺 Вывод tikleap_manager:")
            stdout_lines = []
            stderr_lines = []

            while True:
                # Проверяем завершился ли процесс
                if process.poll() is not None:
                    break

                # Читаем доступные данные
                try:
                    import select

                    ready, _, _ = select.select(
                        [process.stdout, process.stderr], [], [], 1
                    )

                    for stream in ready:
                        if stream == process.stdout:
                            line = stream.readline()
                            if line:
                                line = line.strip()
                                stdout_lines.append(line)
                                logger.info(f"📤 {line}")
                        elif stream == process.stderr:
                            line = stream.readline()
                            if line:
                                line = line.strip()
                                stderr_lines.append(line)
                                logger.warning(f"⚠️ {line}")

                except:
                    # Fallback для систем без select
                    time.sleep(1)

            # Дочитываем оставшиеся данные
            remaining_stdout, remaining_stderr = process.communicate()
            if remaining_stdout:
                for line in remaining_stdout.strip().split("\n"):
                    if line:
                        stdout_lines.append(line)
                        logger.info(f"📤 {line}")

            if remaining_stderr:
                for line in remaining_stderr.strip().split("\n"):
                    if line:
                        stderr_lines.append(line)
                        logger.warning(f"⚠️ {line}")

            return_code = process.returncode
            logger.info(f"🏁 tikleap_manager завершен с кодом: {return_code}")

            if return_code == 0:
                logger.success("✅ tikleap_manager завершен успешно")

                # Ждем немного для завершения записи файлов
                time.sleep(3)

                # Проверяем наличие cookies файла
                if self.cookies_file.exists():
                    logger.success(f"🍪 Cookies найдены: {self.cookies_file}")

                    # Проверим размер и содержимое файла
                    file_size = self.cookies_file.stat().st_size
                    logger.info(f"📏 Размер cookies файла: {file_size} байт")

                    if file_size > 0:
                        try:
                            import json

                            with open(self.cookies_file, "r") as f:
                                cookies_data = json.load(f)

                            if (
                                isinstance(cookies_data, dict)
                                and "cookies" in cookies_data
                            ):
                                cookies_count = len(cookies_data["cookies"])
                                logger.success(
                                    f"✅ Cookies валидны, содержат {cookies_count} элементов"
                                )
                                return True
                            elif isinstance(cookies_data, list):
                                logger.success(
                                    f"✅ Cookies валидны, содержат {len(cookies_data)} элементов"
                                )
                                return True
                            else:
                                logger.warning(
                                    f"⚠️ Неожиданная структура cookies: {type(cookies_data)}"
                                )
                                return True  # Всё равно пробуем использовать

                        except Exception as e:
                            logger.error(f"❌ Ошибка чтения cookies: {e}")
                            return False
                    else:
                        logger.error("❌ Cookies файл пустой")
                        return False
                else:
                    # Поищем cookies файлы в папке
                    all_files = list(self.cookies_dir.iterdir())
                    logger.warning(f"❌ Основной cookies файл не найден")
                    logger.info(
                        f"📁 Файлы в cookies директории: {[f.name for f in all_files]}"
                    )
                    return False
            else:
                logger.error(
                    f"❌ tikleap_manager завершен с ошибкой, код: {return_code}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Исключение при авторизации: {e}")
            import traceback

            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            return False

    async def run_data_collection(self):
        """Запускает сбор данных"""
        try:
            logger.info("📊 Запускаем сбор данных...")

            # Проверяем что client/main.py существует
            if not self.client_script.exists():
                logger.error(f"❌ Файл сбора данных не найден: {self.client_script}")
                return False

            # Проверяем что cookies существуют перед запуском
            if not self.cookies_file.exists():
                logger.error("❌ Cookies файл не найден перед сбором данных")
                return False

            # Меняем рабочую директорию на client
            client_dir = self.project_root / "client"
            logger.info(f"📁 Переходим в директорию: {client_dir}")

            # Устанавливаем переменные окружения
            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.project_root)

            logger.info(f"🚀 Выполняем: python {self.client_script}")

            process = subprocess.Popen(
                [sys.executable, str(self.client_script)],
                cwd=str(client_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
            )

            # Читаем вывод в реальном времени
            logger.info("📺 Вывод сбора данных:")

            try:
                # Устанавливаем таймаут 10 минут
                stdout, stderr = process.communicate(timeout=600)

                # Показываем вывод
                if stdout:
                    for line in stdout.strip().split("\n"):
                        if line:
                            logger.info(f"📤 {line}")

                if stderr:
                    for line in stderr.strip().split("\n"):
                        if line:
                            logger.warning(f"⚠️ {line}")

            except subprocess.TimeoutExpired:
                logger.warning("⏱️ Таймаут сбора данных, завершаем процесс...")
                process.kill()
                stdout, stderr = process.communicate()
                return False

            if process.returncode == 0:
                logger.success("✅ Сбор данных завершен успешно")
                return True
            else:
                logger.error(f"❌ Ошибка сбора данных, код: {process.returncode}")
                return False

        except Exception as e:
            logger.error(f"❌ Исключение при сборе данных: {e}")
            import traceback

            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            return False

    async def run_single_cycle(self):
        """Выполняет один полный цикл: авторизация + сбор данных"""
        logger.info("🔄 Начинаем новый цикл сбора данных")
        start_time = datetime.now()

        try:
            # Шаг 1: Авторизация через tikleap_manager.sh
            auth_success = self.run_auth_via_manager()
            if not auth_success:
                logger.error("❌ Не удалось выполнить авторизацию")
                return False

            # Пауза между авторизацией и сбором данных
            logger.info("⏳ Пауза между авторизацией и сбором данных...")
            await asyncio.sleep(5)

            # Шаг 2: Сбор данных
            data_success = await self.run_data_collection()
            if not data_success:
                logger.error("❌ Не удалось собрать данные")
                return False

            # Успешное завершение цикла
            duration = datetime.now() - start_time
            logger.success(f"🎉 Цикл завершен успешно за {duration}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка в цикле: {e}")
            import traceback

            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            return False

    async def run_scheduler(self, interval_minutes=5):
        """Запускает планировщик с заданным интервалом"""
        logger.info(f"⏰ Запускаем планировщик с интервалом {interval_minutes} минут")

        cycle_count = 0
        while True:
            try:
                cycle_count += 1
                logger.info(f"🔢 Цикл #{cycle_count}")

                # Выполняем цикл
                success = await self.run_single_cycle()

                if success:
                    logger.success(f"✅ Цикл #{cycle_count} завершен успешно")
                else:
                    logger.error(f"❌ Цикл #{cycle_count} завершен с ошибкой")

                # Ждем до следующего запуска
                logger.info(
                    f"😴 Ожидание {interval_minutes} минут до следующего цикла..."
                )
                await asyncio.sleep(interval_minutes * 60)

            except KeyboardInterrupt:
                logger.info("🛑 Получен сигнал остановки")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка планировщика: {e}")
                import traceback

                logger.error(f"🔍 Traceback: {traceback.format_exc()}")
                logger.info("⏳ Ждем 2 минуты перед повтором...")
                await asyncio.sleep(120)


async def main():
    """Главная функция"""
    orchestrator = TikLeapOrchestrator()

    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] == "--single":
            # Запуск одного цикла
            logger.info("🎯 Режим: один цикл")
            success = await orchestrator.run_single_cycle()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "--interval":
            # Запуск с кастомным интервалом
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            logger.info(f"🔄 Режим: планировщик каждые {interval} минут")
            await orchestrator.run_scheduler(interval)
        elif sys.argv[1] == "--auth-only":
            # Только авторизация (для тестирования)
            logger.info("🔐 Режим: только авторизация")
            success = orchestrator.run_auth_via_manager()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "--scrape-only":
            # Только сбор данных (для тестирования)
            logger.info("📊 Режим: только сбор данных")
            success = await orchestrator.run_data_collection()
            sys.exit(0 if success else 1)
        else:
            print("Использование:")
            print("  python main_orchestrator.py --single           # Один цикл")
            print("  python main_orchestrator.py --interval 5       # Каждые 5 минут")
            print(
                "  python main_orchestrator.py --auth-only        # Только авторизация"
            )
            print(
                "  python main_orchestrator.py --scrape-only      # Только сбор данных"
            )
            sys.exit(1)
    else:
        # По умолчанию - планировщик каждые 5 минут
        logger.info("🔄 Режим по умолчанию: планировщик каждые 5 минут")
        await orchestrator.run_scheduler(5)


if __name__ == "__main__":
    asyncio.run(main())
