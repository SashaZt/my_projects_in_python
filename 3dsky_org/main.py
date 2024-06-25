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


def get_random_pause(time_pause):
    return random.uniform(time_pause, time_pause * 2)


# # Функция для переименования архива
# def rename_archive_if_needed(file_name, file_name_archive):
#     if file_name != file_name_archive:
#         archive_extensions = {".zip", ".rar", ".7z"}
#         for archive_ext in archive_extensions:
#             archive_path = os.path.join(temp_path, f"{file_name}{archive_ext}")
#             if os.path.exists(archive_path):
#                 new_archive_path = os.path.join(
#                     temp_path, f"{file_name_archive}{archive_ext}"
#                 )
#                 os.rename(archive_path, new_archive_path)
#                 print(f"Переименован архив {archive_path} -> {new_archive_path}")
#                 break
# Функция для переименования архива
def rename_archive_if_needed(file_name, file_name_archive):
    if file_name != file_name_archive:
        archive_extensions = {".zip", ".rar", ".7z"}
        for archive_ext in archive_extensions:
            archive_path = os.path.join(temp_path, f"{file_name}{archive_ext}")
            if os.path.exists(archive_path):
                new_archive_path = os.path.join(
                    temp_path, f"{file_name_archive}{archive_ext}"
                )
                if os.path.exists(new_archive_path):
                    os.remove(new_archive_path)  # Удаляем файл, если он уже существует
                os.rename(archive_path, new_archive_path)
                print(f"Переименован архив {archive_path} -> {new_archive_path}")
                break


# Функция для принудительного перемещения архива
def move_archive_forcefully(src_path, dst_path):
    if os.path.exists(dst_path):
        os.remove(dst_path)  # Удаляем файл, если он существует
    shutil.move(src_path, dst_path)
    print(f"Перемещен архив {src_path} -> {dst_path}")


# Основная функция
def main(time_pause):
    os.makedirs(temp_path, exist_ok=True)
    os.makedirs(no_img_path, exist_ok=True)

    start_url = "https://b6.3ddd.ru/media/cache/sky_model_new_big_ang_en/"
    archive_extensions = {".zip", ".rar", ".7z"}

    file_names = [
        os.path.splitext(f)[0]
        for f in os.listdir(temp_path)
        if os.path.isfile(os.path.join(temp_path, f))
        and os.path.splitext(f)[1].lower() in archive_extensions
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
        print(file_name)
        # Проверка наличия файлов с изображениями
        image_extensions = {".jpg", ".jpeg", ".png"}
        image_exists = any(
            os.path.exists(os.path.join(temp_path, f"{file_name}{ext}"))
            for ext in image_extensions
        )
        if image_exists:
            print(f"Изображение для {file_name} уже существует.")
            continue  # Пропускаем файл, если изображение уже существует

        # Формируем данные для запроса
        json_data = {
            "query": file_name,
            "order": "relevance",
        }

        # Отправляем запрос на API для поиска модели
        response = requests.post(
            "https://3dsky.org/api/models",
            cookies=cookies,
            headers=headers,
            json=json_data,
        )
        if response.status_code != 200:
            print(
                f"Не удалось получить данные для {file_name}. Код ошибки: {response.status_code}"
            )
            continue  # Пропускаем файл, если запрос не успешен

        json_data = response.json()
        if not (json_data.get("data") and json_data["data"].get("models")):
            print(f"Не удалось найти изображение для {file_name}. Перемещение архива.")
            for ext in archive_extensions:
                archive_path = os.path.join(temp_path, f"{file_name}{ext}")
                if os.path.exists(archive_path):
                    dst_path = os.path.join(no_img_path, f"{file_name}{ext}")
                    move_archive_forcefully(archive_path, dst_path)
                    break
            continue  # Пропускаем файл, если данные модели не найдены

        found_image = False

        # Проходим по всем моделям в данных
        for model in json_data["data"]["models"]:
            if not model.get("images"):
                continue  # Пропускаем модель, если у нее нет изображений

            for i, image_data in enumerate(model["images"]):
                if image_data["file_name"] == file_name:
                    found_image = True

                    if i == 0:  # Если найденное изображение первое, скачиваем его
                        image_url_raw = image_data["web_path"]
                        image_url = f"{start_url}{image_url_raw}"
                        response = requests.get(image_url)

                        match = re.search(
                            r"/([^/]+)\.(jpg|jpeg|png)$", image_url, re.IGNORECASE
                        )
                        if match:
                            file_name_archive = match.group(1)
                            ext = match.group(2)
                            image_name = f"{file_name_archive}.{ext}"
                            image_path = os.path.join(temp_path, image_name)

                            if response.status_code == 200:
                                with open(image_path, "wb") as f:
                                    f.write(response.content)
                                print(f"Изображение сохранено в {image_path}")
                            else:
                                print(
                                    f"Не удалось скачать изображение. Код ошибки: {response.status_code}"
                                )

                            # Проверка и переименование архива после скачивания изображения
                            rename_archive_if_needed(file_name, file_name_archive)

                        break
                    elif i > 0:
                        # Проверяем наличие архива с таким же именем и удаляем его
                        for archive_ext in archive_extensions:
                            archive_path = os.path.join(
                                temp_path, f"{file_name}{archive_ext}"
                            )
                            if os.path.exists(archive_path):
                                os.remove(archive_path)
                                print(f"Удален архив {archive_path}")
                        break
            if found_image:
                break

        if not found_image:
            # Если запрашиваемое имя файла не найдено, берем первое изображение из списка
            for model in json_data["data"]["models"]:
                if not model.get("images"):
                    continue  # Пропускаем модель, если у нее нет изображений

                first_image_data = model["images"][0]
                image_url_raw = first_image_data["web_path"]
                image_url = f"{start_url}{image_url_raw}"
                response = requests.get(image_url)

                match = re.search(
                    r"/([^/]+)\.(jpg|jpeg|png)$", image_url, re.IGNORECASE
                )
                if match:
                    file_name_archive = match.group(1)
                    ext = match.group(2)
                    image_name = f"{file_name_archive}.{ext}"
                    image_path = os.path.join(temp_path, image_name)

                    if response.status_code == 200:
                        with open(image_path, "wb") as f:
                            f.write(response.content)
                        print(f"Изображение сохранено в {image_path}")
                    else:
                        print(
                            f"Не удалось скачать изображение. Код ошибки: {response.status_code}"
                        )

                    # Проверка и переименование архива после скачивания изображения
                    rename_archive_if_needed(file_name, file_name_archive)

                    found_image = True
                    break

        # Если изображение так и не было найдено и скачано, перемещаем архив
        if not found_image:
            print(f"Не удалось найти изображение для {file_name}. Перемещение архива.")
            for ext in archive_extensions:
                archive_path = os.path.join(temp_path, f"{file_name}{ext}")
                if os.path.exists(archive_path):
                    shutil.move(archive_path, no_img_path)
                    print(f"Перемещен архив {archive_path} -> {no_img_path}")
                    break

        # Пауза перед обработкой следующего файла
        random_pause = get_random_pause(time_pause)
        time.sleep(random_pause)


if __name__ == "__main__":
    print("Введите пожалуйста в секундах паузу")
    time_pause = int(input())
    main(time_pause)
