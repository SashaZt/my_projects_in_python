from logger_setup import logger
import sys
import os
import subprocess
from pathlib import Path
import time

# Важное сообщение для пользователя с задержкой на 20 секунд
logger.warning(
    "ВАЖНО: Перед запуском этого скрипта убедитесь, что вы активировали виртуальное окружение вручную."
)
logger.warning("Для этого выполните следующие команды в командной строке:")
logger.warning(r".\venv\Scripts\activate")
logger.warning("Затем обновите Playwright с помощью команды:")
logger.warning("pip install --upgrade playwright")
logger.warning("Этот скрипт продолжит выполнение через 20 секунд...")
time.sleep(20)


def set_playwright_browsers_path():
    browsers_path = Path.cwd() / "pw-browsers"
    command = f"[Environment]::SetEnvironmentVariable('PLAYWRIGHT_BROWSERS_PATH', '{browsers_path}', 'User')"

    try:
        subprocess.run(["powershell", "-Command", command], check=True)
        logger.info(f"Постоянный путь для браузеров установлен: {browsers_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Не удалось установить переменную окружения: {e}")


def check_playwright_browsers_path():
    command = (
        "[Environment]::GetEnvironmentVariable('PLAYWRIGHT_BROWSERS_PATH', 'User')"
    )
    result = subprocess.run(
        ["powershell", "-Command", command], capture_output=True, text=True
    )

    if result.stdout.strip():
        logger.info(
            f"Текущая переменная PLAYWRIGHT_BROWSERS_PATH: {result.stdout.strip()}"
        )
    else:
        logger.error("Переменная PLAYWRIGHT_BROWSERS_PATH не установлена.")


def upgrade_playwright():
    logger.info("Обновляем пакет Playwright до последней версии.")
    try:
        # Проверяем, если мы уже в виртуальном окружении
        if not hasattr(sys, "real_prefix"):
            logger.error("Виртуальное окружение не активировано!")
            return

        # Обновляем playwright
        process = subprocess.Popen(
            [sys.executable, "-m", "pip", "install", "--upgrade", "playwright"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        for line in process.stdout:
            logger.info(line.strip())

        process.wait()  # Ждем завершения процесса

        if process.returncode == 0:
            logger.info("Пакет Playwright успешно обновлен.")
        else:
            logger.error(
                f"Произошла ошибка при обновлении пакета Playwright с кодом {process.returncode}"
            )

    except Exception as e:
        logger.error(f"Произошла ошибка при обновлении пакета Playwright: {e}")


def main_install_playwright_chromium():
    set_playwright_browsers_path()
    check_playwright_browsers_path()

    # Обновление Playwright перед установкой браузера
    # upgrade_playwright()

    logger.info("Начинаем установку браузера Playwright Chromium.")
    try:
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(Path.cwd() / "pw-browsers")

        # Используем Popen для потокового вывода
        process = subprocess.Popen(
            ["python", "-m", "playwright", "install", "chromium"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=os.environ,
        )

        for line in process.stdout:
            logger.info(line.strip())

        process.wait()  # Ждем завершения процесса

        if process.returncode == 0:
            logger.info("Браузер Chromium успешно установлен.")
        else:
            logger.error(
                f"Произошла ошибка при установке браузера Chromium с кодом {process.returncode}"
            )

    except Exception as e:
        logger.error(f"Произошла ошибка при установке браузера Chromium: {e}")


def find_chromium_installation():
    possible_paths = [
        Path.cwd() / "pw-browsers",
        Path.home() / "AppData" / "Local" / "ms-playwright",
    ]

    for path in possible_paths:
        logger.info(f"Проверка пути: {path}")
        if path.exists() and any(path.glob("**/chromium")):
            return path

    return None


def remove_playwright_browsers_path():
    command = "[Environment]::SetEnvironmentVariable('PLAYWRIGHT_BROWSERS_PATH', $null, 'User')"

    try:
        subprocess.run(["powershell", "-Command", command], check=True)
        logger.info("Переменная окружения PLAYWRIGHT_BROWSERS_PATH успешно удалена.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Не удалось удалить переменную окружения: {e}")


if __name__ == "__main__":
    main_install_playwright_chromium()
