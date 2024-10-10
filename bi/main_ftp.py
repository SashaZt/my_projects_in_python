import requests
from pathlib import Path
from ftplib import FTP
import os

# Настройки FTP сервера
ftp_host = "ds70.mirohost.net"
ftp_user = "babyfullj"
ftp_pass = "jML6Wf6O123"
ftp_directory = "/admin.babyfull.com.ua/bi_images/"


# Подключаемся к FTP
def connect_ftp():
    ftp = FTP(ftp_host)
    ftp.login(user=ftp_user, passwd=ftp_pass)
    ftp.cwd(ftp_directory)
    return ftp


# Получаем список файлов в FTP директории
def get_ftp_file_list(ftp):
    return ftp.nlst()


# Загрузка файла на FTP сервер
def upload_to_ftp(ftp, file_name, file_content):
    with ftp.storbinary(f"STOR {file_name}", file_content) as f:
        print(f"Загружено на FTP: {file_name}")


# Основной код
def download_and_upload_images(
    images, max_images, cookies, headers, proxies_dict, img_directory
):
    ftp = connect_ftp()  # Подключаемся к FTP серверу
    ftp_files = get_ftp_file_list(ftp)  # Получаем список файлов на FTP сервере

    for index, images_url in enumerate(images, start=1):
        if index > max_images:  # Прерываем цикл, если уже обработано max_images
            break
        url_image = f'https://bi.ua{images_url.get("content")}'
        file_name = Path(url_image).name  # Извлекаем имя файла из URL

        if file_name not in ftp_files:  # Проверяем, нет ли файла на FTP сервере
            try:
                # Делаем запрос к URL
                response = requests.get(
                    url_image,
                    cookies=cookies,
                    headers=headers,
                    proxies=proxies_dict,
                )
                response.raise_for_status()  # Проверяем, успешен ли запрос

                # Загружаем файл на FTP
                upload_to_ftp(ftp, file_name, response.content)

            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка при загрузке {url_image}: {e}")

    ftp.quit()  # Отключаемся от FTP сервера


# Пример вызова функции
# download_and_upload_images(images, 3, cookies, headers, proxies_dict, img_directory)
if __name__ == "__main__":
    ftp = connect_ftp()  # Подключаемся к FTP серверу
    ftp_files = get_ftp_file_list(ftp)  # Получаем список файлов на FTP сервере
    print(ftp_files)
    print(len(ftp_files))
    ftp.quit()  # Отключаемся от FTP сервера
