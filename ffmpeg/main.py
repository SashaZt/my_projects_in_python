import subprocess

def resize_video(input_video_path, output_video_path, width=1920, height=1080):
    """
    Изменяет разрешение видео с использованием FFmpeg, сохраняя оригинальные битрейты и кодеки.

    Args:
    - input_video_path: Путь к исходному видеофайлу.
    - output_video_path: Путь, куда будет сохранено видео с измененным разрешением.
    - width: Желаемая ширина видео в пикселях.
    - height: Желаемая высота видео в пикселях.
    """
    cmd = [
        'ffmpeg',
        '-i', input_video_path,
        '-vf', f"scale={width}:{height}:force_original_aspect_ratio=decrease",
        '-c:v', 'libx264',  # Указываем кодек видео, если хотите сохранить использование определенного кодека
        '-preset', 'veryfast',  # Быстрее кодирует видео, возможно, с небольшим увеличением размера файла. Можно адаптировать в зависимости от ваших нужд.
        '-crf', '23',  # CRF может быть адаптирован для управления качеством. Меньшее значение = выше качество.
        '-c:a', 'copy',  # Копирование аудиодорожки без изменений
        output_video_path
    ]
    subprocess.run(cmd)

# Пример использования
input_video = 'C:\\seminar\\Eng_01\\video1232928904.mp4'
output_video = 'C:\\seminar\\Eng_01\\video1232928904_1080.mp4'
resize_video(input_video, output_video)
