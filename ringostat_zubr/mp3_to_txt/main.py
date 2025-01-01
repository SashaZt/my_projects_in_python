import warnings
from pathlib import Path

import whisper
from configuration.logger_setup import logger

# Путь к папкам и файлу для данных
current_directory = Path.cwd()
configuration_directory = current_directory / "configuration"
call_recording_directory = current_directory / "call_recording"
call_recording_directory.mkdir(parents=True, exist_ok=True)

# Подавляем FutureWarning и UserWarning
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def transcribe_audio_files():
    """
    Транскрибирует файлы .mp3 из директории call_recording_directory,
    создает .txt файлы с результатами транскрипции.
    """
    logger.info("Старт транскрибирования файлов")
    try:
        # Явное указание использования CPU
        logger.info("Загрузка модели Whisper...")
        model = whisper.load_model("base", device="cpu")
        logger.info("Модель Whisper успешно загружена")

        # Перебор всех файлов .mp3 в директории
        for file_path in call_recording_directory.glob("*.mp3"):
            logger.info(f"Проверка файла: {file_path}")
            if not file_path.exists():
                logger.error(f"Файл не найден: {file_path}")
                continue

            txt_file_path = file_path.with_suffix(
                ".txt"
            )  # Путь к .txt файлу с тем же именем

            # Пропускаем, если транскрипция уже выполнена
            if txt_file_path.exists():
                logger.info(f"Транскрипция уже существует: {txt_file_path}")
                continue

            logger.info(f"Транскрибирование файла: {file_path}")

            # Транскрибирование аудиофайла
            try:
                result = model.transcribe(str(file_path))
                # Запись текста в файл
                with open(txt_file_path, "w", encoding="utf-8") as txt_file:
                    txt_file.write(result["text"])
                logger.info(f"Файл транскрибирован и сохранен как: {txt_file_path}")
            except Exception as transcribe_error:
                logger.error(
                    f"Ошибка при транскрибировании файла {file_path}: {transcribe_error}"
                )

    except Exception as e:
        logger.error(f"Общая ошибка при транскрибировании: {e}")


if __name__ == "__main__":
    transcribe_audio_files()
