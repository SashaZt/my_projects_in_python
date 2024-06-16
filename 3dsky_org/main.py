import time
import requests
import json
import re
import os
import random
import shutil


current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
no_img_path = os.path.join(temp_path, "no_img")
os.makedirs(temp_path, exist_ok=True)
os.makedirs(no_img_path, exist_ok=True)


def get_random_pause(time_pause):
    return random.uniform(time_pause, time_pause * 2)


# Функция для переименования архива
def rename_archive_if_needed(file_name, file_name_archive):
    if file_name != file_name_archive:
        archive_extensions = {".zip", ".rar", ".7z"}
        for ext in archive_extensions:
            archive_path = os.path.join(temp_path, f"{file_name}{ext}")
            if os.path.exists(archive_path):
                new_archive_path = os.path.join(temp_path, f"{file_name_archive}{ext}")
                os.rename(archive_path, new_archive_path)
                print(f"Переименован архив {archive_path} -> {new_archive_path}")
                break


# Основная функция
def main(time_pause):
    start_url = "https://b6.3ddd.ru/media/cache/sky_model_new_big_ang_en/"

    file_names = [
        os.path.splitext(f)[0]
        for f in os.listdir(temp_path)
        if os.path.isfile(os.path.join(temp_path, f))
        and os.path.splitext(f)[1].lower() in {".zip", ".rar", ".7z"}
    ]

    cookies = {
        "frontsrv": "k90",
        "CookieConsent_en": "1%7C1747401714",
        "PHPSESSID": "ba7268315e4e1c392ee45cdb8f7d68d9",
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "DNT": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    for file_name in file_names:

        json_data = {
            "query": file_name,
            "order": "relevance",
        }
        response = requests.post(
            "https://3dsky.org/api/models",
            cookies=cookies,
            headers=headers,
            json=json_data,
        )
        file_name_jpeg = f"{file_name}.jpeg"
        jpeg_path = os.path.join(temp_path, file_name_jpeg)
        if not os.path.exists(jpeg_path):
            try:
                json_data = response.json()
                if (
                    json_data["data"]["models"]
                    and json_data["data"]["models"][0]["images"]
                ):
                    image_url_raw = json_data["data"]["models"][0]["images"][0][
                        "web_path"
                    ]
                    image_url = f"{start_url}{image_url_raw}"
                    response = requests.get(image_url)

                    match = re.search(r"/([^/]+)\.jpeg$", image_url)
                    file_name_archive = match.group(1)
                    image_name = f"{file_name_archive}.jpeg"
                    image_path = os.path.join(temp_path, image_name)

                    # Проверка и переименование архива
                    rename_archive_if_needed(file_name, file_name_archive)

                    if response.status_code == 200:
                        with open(image_path, "wb") as f:
                            f.write(response.content)
                        print(f"Изображение сохранено в {image_path}")
                    else:
                        print(
                            f"Не удалось скачать изображение. Код ошибки: {response.status_code}"
                        )
                else:
                    raise IndexError("No images found")
            except (KeyError, IndexError):
                print(
                    f"Не удалось найти изображение для {file_name}. Перемещение архива."
                )
                archive_extensions = {".zip", ".rar", ".7zip"}
                for ext in archive_extensions:
                    archive_path = os.path.join(temp_path, f"{file_name}{ext}")
                    if os.path.exists(archive_path):
                        shutil.move(archive_path, no_img_path)
                        print(f"Перемещен архив {archive_path} -> {no_img_path}")
                        break
            random_pause = get_random_pause(time_pause)
            time.sleep(random_pause)


if __name__ == "__main__":
    print("Введите пожалуйста в секундах паузу")
    time_pause = int(input())
    main(time_pause)
