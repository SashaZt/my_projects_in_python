import os
import re
import subprocess
from pathlib import Path

import requests


def parse_m3u8_content(m3u8_content, output_dir="ts_files"):
    """Parse M3U8 content and download TS segments"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    ts_urls = re.findall(r"https?://[^\s]+\.ts\?[^\s]+", m3u8_content)
    ts_files = []
    print(f"Найдено {len(ts_urls)} сегментов для скачивания")
    for i, ts_url in enumerate(ts_urls):
        ts_file_path = output_path / f"segment_{i:03d}.ts"
        if ts_file_path.exists():
            print(f"Файл {ts_file_path} уже существует, пропускаем скачивание")
            ts_files.append(ts_file_path)
            continue
        print(f"Скачивание сегмента {i+1}/{len(ts_urls)}: {ts_url}")
        try:
            response = requests.get(ts_url, timeout=30, stream=True)
            response.raise_for_status()
            with open(ts_file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            ts_files.append(ts_file_path)
            print(f"✓ Сегмент {i+1} скачан успешно")
        except requests.RequestException as e:
            print(f"✗ Ошибка при скачивании сегмента {i+1}: {e}")
    return ts_files


def merge_video_and_audio(
    video_ts_files, audio_ts_files, output_file="output_with_audio.mp4"
):
    """Merge video and audio TS files into a single MP4 file."""
    try:
        # Создаём временные файлы со списками сегментов
        video_filelist = Path("video_filelist.txt")
        audio_filelist = Path("audio_filelist.txt")

        with open(video_filelist, "w", encoding="utf-8") as f:
            for ts_file in video_ts_files:
                abs_path = Path(ts_file).resolve()
                f.write(f"file '{abs_path}'\n")

        with open(audio_filelist, "w", encoding="utf-8") as f:
            for ts_file in audio_ts_files:
                abs_path = Path(ts_file).resolve()
                f.write(f"file '{abs_path}'\n")

        print(
            f"Объединяем {len(video_ts_files)} видеосегментов и {len(audio_ts_files)} аудиосегментов в {output_file}..."
        )

        # Временные файлы для видео и аудио
        temp_video = "temp_video.mp4"
        temp_audio = "temp_audio.mp4"

        # Объединяем видеосегменты
        cmd_video = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(video_filelist),
            "-c:v",
            "copy",
            "-an",
            "-y",
            temp_video,
        ]
        subprocess.run(cmd_video, check=True, capture_output=True, text=True)

        # Объединяем аудиосегменты
        cmd_audio = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(audio_filelist),
            "-c:a",
            "aac",
            "-vn",
            "-y",
            temp_audio,
        ]
        subprocess.run(cmd_audio, check=True, capture_output=True, text=True)

        # Объединяем видео и аудио в итоговый файл
        cmd_merge = [
            "ffmpeg",
            "-i",
            temp_video,
            "-i",
            temp_audio,
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-map",
            "0:v",
            "-map",
            "1:a",
            "-shortest",  # Урезаем по самому короткому потоку (286 сегментов)
            "-y",
            output_file,
        ]
        subprocess.run(cmd_merge, check=True, capture_output=True, text=True)

        print(f"✓ Видео с аудио успешно сохранено как {output_file}")

        # Удаляем временные файлы
        video_filelist.unlink()
        audio_filelist.unlink()
        if Path(temp_video).exists():
            Path(temp_video).unlink()
        if Path(temp_audio).exists():
            Path(temp_audio).unlink()

        return True

    except subprocess.CalledProcessError as e:
        print(f"✗ Ошибка ffmpeg: {e}")
        print(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"✗ Общая ошибка: {e}")
        return False


def cleanup_ts_files(ts_files, output_dir):
    """Clean up downloaded TS files after successful conversion"""
    try:
        for ts_file in ts_files:
            if Path(ts_file).exists():
                Path(ts_file).unlink()
        output_path = Path(output_dir)
        if output_path.exists() and not any(output_path.iterdir()):
            output_path.rmdir()
        print(f"✓ Папка {output_dir} и файлы удалены")
    except Exception as e:
        print(f"⚠ Ошибка при удалении: {e}")


def find_best_quality(master_m3u8_content):
    """
    Parse master.m3u8 content and return URLs for the highest quality video and audio streams.

    Args:
        master_m3u8_content (str): Content of the master.m3u8 file.

    Returns:
        tuple: (video_url, audio_url) - URLs for the highest quality video and audio playlists.
    """
    try:
        # Разделяем содержимое на строки
        lines = master_m3u8_content.strip().split("\n")

        # Переменные для хранения лучшего качества
        max_bandwidth = 0
        best_video_url = None
        best_audio_group = None
        best_resolution = (0, 0)  # (width, height)

        # Словарь для хранения аудиопотоков по GROUP-ID
        audio_urls = {}

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Собираем аудиопотоки
            if line.startswith("#EXT-X-MEDIA:TYPE=AUDIO"):
                # Извлекаем GROUP-ID и URI
                group_id_match = re.search(r'GROUP-ID="([^"]+)"', line)
                uri_match = re.search(r'URI="([^"]+)"', line)
                if group_id_match and uri_match:
                    group_id = group_id_match.group(1)
                    audio_urls[group_id] = uri_match.group(1)

            # Ищем видеопотоки
            elif line.startswith("#EXT-X-STREAM-INF:"):
                # Извлекаем BANDWIDTH, RESOLUTION и AUDIO
                bandwidth_match = re.search(r"BANDWIDTH=(\d+)", line)
                resolution_match = re.search(r"RESOLUTION=(\d+x\d+)", line)
                audio_group_match = re.search(r'AUDIO="([^"]+)"', line)

                if bandwidth_match and resolution_match and audio_group_match:
                    bandwidth = int(bandwidth_match.group(1))
                    resolution = tuple(map(int, resolution_match.group(1).split("x")))
                    audio_group = audio_group_match.group(1)

                    # Обновляем лучший поток, если разрешение выше или битрейт больше при равном разрешении
                    current_resolution_area = resolution[0] * resolution[1]
                    best_resolution_area = best_resolution[0] * best_resolution[1]

                    if current_resolution_area > best_resolution_area or (
                        current_resolution_area == best_resolution_area
                        and bandwidth > max_bandwidth
                    ):
                        max_bandwidth = bandwidth
                        best_resolution = resolution
                        best_video_url = lines[i + 1].strip()
                        best_audio_group = audio_group

                i += 1  # Пропускаем следующую строку (URL видео)
            i += 1

        if (
            not best_video_url
            or not best_audio_group
            or best_audio_group not in audio_urls
        ):
            print("✗ Не удалось найти подходящий видео- или аудиопоток")
            return None, None

        best_audio_url = audio_urls[best_audio_group]
        print(
            f"Найден лучший видеопоток: {best_resolution} (BANDWIDTH={max_bandwidth}), аудиопоток: {best_audio_group}"
        )
        return best_video_url, best_audio_url

    except Exception as e:
        print(f"✗ Ошибка при парсинге мастер-плейлиста: {e}")
        return None, None


def main():
    with open("master.m3u8", "r", encoding="utf-8") as f:
        master_m3u8_content = f.read()
    # Находим лучший видео- и аудиопоток
    video_m3u8_url, audio_m3u8_url = find_best_quality(master_m3u8_content)
    if not video_m3u8_url or not audio_m3u8_url:
        print("✗ Не удалось определить URL для видео или аудио")
        return

    # Скачиваем содержимое плейлистов
    print("Загружаем видеоплейлист...")
    video_response = requests.get(video_m3u8_url, timeout=30)
    video_response.raise_for_status()
    video_m3u8_content = video_response.text

    print("Загружаем аудиоплейлист...")
    audio_response = requests.get(audio_m3u8_url, timeout=30)
    audio_response.raise_for_status()
    audio_m3u8_content = audio_response.text

    # Скачиваем TS-сегменты
    video_ts_files = parse_m3u8_content(video_m3u8_content, output_dir="video_ts_files")
    audio_ts_files = parse_m3u8_content(audio_m3u8_content, output_dir="audio_ts_files")

    # Проверяем количество сегментов
    print(
        f"Скачано видеосегментов: {len(video_ts_files)}, аудиосегментов: {len(audio_ts_files)}"
    )

    # Объединяем видео и аудио
    output_file = "sky_news_video_with_audio.mp4"
    success = merge_video_and_audio(video_ts_files, audio_ts_files, output_file)

    # Удаляем временные файлы
    if success:
        cleanup_ts_files(video_ts_files, "video_ts_files")
        cleanup_ts_files(audio_ts_files, "audio_ts_files")


if __name__ == "__main__":
    main()
