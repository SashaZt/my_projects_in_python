# /utils/file_utils.py
import gzip
import shutil
from pathlib import Path

from config.logger import logger


def create_directories(*dirs: Path) -> None:
    """Создает необходимые директории."""
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Директория создана или уже существует: {directory}")


def extract_gz_files(input_dir: Path, output_dir: Path) -> None:
    """Распаковывает .xml.gz файлы."""
    output_dir.mkdir(parents=True, exist_ok=True)

    gz_files = list(input_dir.glob("*.gz"))
    total_files = len(gz_files)
    extracted_count = 0

    for gz_file in gz_files:
        output_file = output_dir / gz_file.stem
        try:
            with gzip.open(gz_file, "rb") as f_in:
                with open(output_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            extracted_count += 1
            logger.info(
                f"Распакован файл {gz_file.name} ({extracted_count}/{total_files})"
            )
        except Exception as e:
            logger.error(f"Ошибка при распаковке {gz_file.name}: {e}")

    logger.info(f"Распаковано {extracted_count} из {total_files} файлов")
