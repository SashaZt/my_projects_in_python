import yt_dlp
import os
from pydub import AudioSegment


channel_url = 'https://www.youtube.com/@flavourtrip/videos'

def get_all_video_in_channel(channel_url):
    ydl_opts = {'ignoreerrors': True}
    video_info = []  # список кортежей вида [(url1, title1), (url2, title2), ...]
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        channel_dict = ydl.extract_info(channel_url, download=False)
        if 'entries' in channel_dict:
            for video in channel_dict['entries']:
                if video is not None:
                    url = video['webpage_url']
                    title = video['title']
                    video_info.append((url, title))
    return video_info

def main(video_info):
    ydl_opts = {
        'proxy': 'http://proxy_alex:DbrnjhbZ88@141.145.205.4:31281',
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.mp3',
        'socket_timeout': 60,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '256',
        }],
    }
    for url, title in video_info:
        if not os.path.isfile(f"downloads/{title}.mp3"):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])  # обратите внимание на квадратные скобки вокруг url

def all_in_one():
    # Предположим, что все ваши файлы находятся в каталоге 'downloads'
    download_dir = 'downloads'

    # Соберите все mp3 файлы в один список
    mp3_files = [f for f in os.listdir(download_dir) if f.endswith('.mp3')]

    # Создайте пустой аудиосегмент для хранения объединенного аудио
    combined = AudioSegment.empty()

    # Создайте паузу в 5 секунд
    pause = AudioSegment.silent(duration=5000)  # длительность в миллисекундах

    # Пройдите по каждому файлу, прочитайте его, добавьте паузу и добавьте его к combined
    for file in mp3_files:
        path = os.path.join(download_dir, file)
        audio = AudioSegment.from_mp3(path)
        combined += audio + pause

    # Экспортируйте объединенный аудиофайл
    combined.export("combined.mp3", format='mp3')
if __name__ == '__main__':
    urls = get_all_video_in_channel(channel_url)
    main(urls)
    # all_in_one()
