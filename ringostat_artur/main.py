import requests
from pydub import AudioSegment
import os
from openai import OpenAI


wav_url = "https://app.ringostat.com/recordings/ua0_-1731315881.12669683.wav"  # Замените на URL файла WAV
file_name = os.path.basename(wav_url)
wav_file = file_name
mp3_file = file_name.replace(".wav", ".mp3")

headers = {
    "accept": "*/*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "dnt": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
}

cookies = {
    "rngst-gdpr": "true",
    "intercom-id-berz4v0w": "519383ba-6f3a-4da5-ba0f-9114e5811b4e",
    "rngstsession": "9d594dc77de186b6a0de40ae5350b3bc",
}

params = {
    "token": "aac6ac28eb1e4c3c0e0acbf28dd7c1ab",
}
api_key = "api_key"
client = OpenAI(api_key=api_key)


def download_wav(url, output_path, headers=None, cookies=None, params=None):
    if os.path.exists(output_path):
        print(f"File {output_path} already exists. Skipping download.")
        return
    try:
        response = requests.get(
            url, stream=True, headers=headers, cookies=cookies, params=params
        )
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            print(f"Downloaded: {output_path}")
        else:
            print(f"Failed to download file: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")


def convert_wav_to_mp3(wav_path, mp3_path):
    try:
        audio = AudioSegment.from_wav(wav_path)
        audio.export(mp3_path, format="mp3")
        print(f"Converted to MP3: {mp3_path}")
        # Удаляем wav файл, если mp3 файл успешно создан
        if os.path.exists(mp3_path):
            os.remove(wav_path)
            print(f"Removed: {wav_path}")
    except Exception as e:
        print(f"Failed to convert file: {e}")


# Функция для транскрибации аудиофайла с использованием OpenAI API
def transcribe_audio():
    # Открываем аудиофайл для чтения
    audio_file = open(mp3_file, "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1", file=audio_file
    )
    print(transcription.text)


if __name__ == "__main__":
    # Скачиваем wav файл
    # download_wav(wav_url, wav_file, headers=headers, cookies=cookies, params=params)

    # # Конвертируем wav в mp3
    # if os.path.exists(wav_file):
    #     convert_wav_to_mp3(wav_file, mp3_file)
    transcribe_audio()
