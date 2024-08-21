import os

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(Path.cwd() / "pw-browsers")
try:
    result = subprocess.run(
        ["python", "-m", "playwright", "install", "chromium"],
        check=True,
        capture_output=True,
        text=True,
    )
    logger.info("Браузер Chromium успешно установлен.")
    logger.info(f"Вывод установки: {result.stdout}")
except subprocess.CalledProcessError as e:
    logger.error(f"Произошла ошибка при установке браузера Chromium: {e}")
    logger.error(
        f"Ошибка вывода: {e.stderr if e.stderr else 'Нет дополнительной информации.'}"
    )
