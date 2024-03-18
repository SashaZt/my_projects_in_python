import pandas as pd
import requests
import os
def main():
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    proxies = {'http': 'http://80.77.34.218:9999', 'https': 'http://80.77.34.218:9999'}
    # Загрузка CSV-файла в DataFrame
    df = pd.read_csv('photo_04.csv', delimiter=';')

    # Пропускаем заголовок, если он есть
    df = df.iloc[1:]
    for index, row in df.iterrows():
        modified_row = row.apply(lambda x: x.replace(' ', '_') if isinstance(x, str) else x)

        # Собираем имя фото
        name_photo = f"{modified_row[0]}_{modified_row[1]}_{modified_row[2]}_{modified_row[3]}_{modified_row[4]}"
        # # Проверяем, существуют ли фото с различными номерами
        # for i in range(5, 14):
        #     if pd.notnull(row[i]):
        #         # Путь к файлу фото с номером i
        #         photo_path = f"Фото_паспорта/{name_photo}_{i - 4}.jpg"
        #
        #         # Проверяем, существует ли файл фото
        #         if os.path.exists(photo_path):
        #             print(f"Файл {photo_path} уже существует. Пропускаем итерацию.")
        #             continue
        #
        #         # Получаем URL фото
        #         photo_url = row[i]
        #
        #         # Загружаем фото
        #         response = requests.get(photo_url)
        #
        #         # Проверяем успешность запроса
        #         if response.status_code == 200:
        #             # Открываем файл для записи фото
        #             with open(photo_path, 'wb') as photo_file:
        #                 # Записываем содержимое фото в файл
        #                 photo_file.write(response.content)
        #         else:
        #             print(f"Не удалось загрузить фото для {name_photo}")
        #
        photo_path = f"Другие_справки_фото/{name_photo}_09.jpg"
        if os.path.exists(photo_path):
            continue
        try:
            photo_url = row[13]
        except:
            continue
        # print(name_photo, photo_url)
        # photo_url = row[5].replace(" ", "%20")
        try:
            response = requests.get(photo_url, headers=header) #, proxies=proxies
            # print(response.status_code, photo_url)
            if response.status_code == 200:
                with open(photo_path, 'wb') as photo_file:
                    photo_file.write(response.content)
            else:
                print(f"Не удалось загрузить фото для {row[0]}")
        except:
            continue

if __name__ == '__main__':
    main()
