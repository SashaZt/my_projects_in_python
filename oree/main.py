import requests
import json
import glob
import html
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import csv
import os
import json
import pandas as pd
from datetime import datetime


current_directory = os.getcwd()
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, "temp")
json_path = os.path.join(temp_path, "json")
html_path = os.path.join(temp_path, "html")


def creative_folders():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, json_path,html_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # # Удалите файлы из папок list и product
    # for folder in [list_path, product_path, img_path]:
    #     files = glob.glob(os.path.join(folder, '*'))
    #     for f in files:
    #         if os.path.isfile(f):
    #             os.remove(f)


def get_requests():
    cookies = {
        "lang": "uk-UA",
        "ASP.NET_SessionId": "m31wppeh0k5d1pdnibzaz1rk",
        ".AspNet.Cookies": "Ziw5UIZ-ZFcD9xqR90RTgdlvcW7mc8FQ6sWCPvFzuYJYFen0z0dNTlDwDh9bp4yXKrLeVF5zs-ty3JNbIVAkMAdVdgwO25Zd5YhxMM3h94oYkaVDnFndl_LIDlm_HAP6q_0K28vWDfftNprJAZ70XXaJhQAYzgxTsF3QSQuJGEOzUIbXuCah7WtHi9mubTcxWDxfX_AOyYmAgCq9_6xSvjGWPhUtLIblbat_1yaqxy7S552aOiTjQNHg6Bpr7RHRLX8422Q4616x0odp8JyDv_bwzg8DHYHtXXTUUsavxvPY0Q2Ll45SaLdCFy7faxAAkxXt9hIJd1HVrUAVhC6CvuHBSjE3QbH3B5CH2izQvQOPMrVFzF-_2H9Z-k5p0sNcR32tXdD-bDP5OcJ1gRxQcsaIa8Oumw5AzKs0kscHVVwjtxGjcHdLaKI8ADeFQjtZlax1Z-jWjQrUNsYa4P4nZaOpapvfqf9YRxxRUVsdr108T2d4h_DRL25cKWmuzpsY5GrhsdY7uMuxqVpO8xTU2bqBJ4fc6nC55TcdpSZhXt8dON43auUX8Qys9DLnOC_Z_iqfSs7uD_ewTeW3Os8RT_S8XLxrpgXCR4JCy7LnJEjZlovu9e9Usu8RMMOBs-aD9H4ki1UyDI_9aR3Yi85Gz9avYpOMTg0J3cWBMCZjfcSWBbQaN1pvdgR_Nw3adzZraI87G8_731_7OxkYpn_sgWv8Om0QPoZ6ZIR5Weotx5nPhUqoITA5HtVbMe8h26X7N49jxfY-zNxrByXkrNHAeC6DTflVS54gIzFfvlndjhKSsNsGesmll2DQPM4RjjA_YKv2wTh9zbDHdItvzSoizacS8UawUfAiVp_l5ybJ32M0gKsKqXYKW_iQobyk9OF-ZxEcyubqLS2aUKPqjTOt_OPqRnwfQkytEyt5xH4GKO0ZReDEIyHIEukJRgB96-EP8ROXwfcHj3Cj-fbyTgvEEdfJwG1-GRzNHHTz9FpK0kycs58cyxe2Z1nsX_at14axprXNdYFnFdr-i3uDAlGGKqGIBBC5int8F3pxUkO-A7yDVBaDiWvSCV9BtfHTTDAW5mv5JfiWUs4m28h60K1QRroKpx3PK8TP4i_KZxq-xtmLzYnGURaODwHpH2Qysoy59dEAoXJqmY7LttCYYgVy8dKz1m7yi5-KeYRdoFalv17x5cdrlEyzYmWCFM2n2-9-2aKXUIxRRRKtC-eUQCqmpoJmEacHaZeilNOW_kQcADpFx6Pc_X1BVr2L7huomb3SEozD1rfjb1LDFTdfYYyi7zt-yQzRaS2kYXLto4jrMRi583sFXQd-sB16UJ6DZBnS_iaShCm2hGyOxWjss9Prikhmearw-Amqp4RkCCJ-Z8imz3S5zRzC6QVcp2EoidmMj_i4kxWGLkzhrYrtRI7BHG6pZi8cXsdKLfQkWQzCysR3Y_VbCIViM5sQCaraE50AtU1kqEiO6a7VKgP4Y7BTACOJK-6hOt4Mj_Y4NwSGReEJCzY-Lyu8fBN1NG-Y71YFpXyV20KcsTgOdu3RKcv8NmUo4wkAaRh04sNRXIKSfG_ZHWoclv5MbyZXq9P8XT350LONkBY59yfRhTG1qEfie0VN7UKv0LzMojT9vquk4GwmIPIFNpSnOAEpFy9eEP6ussAZBAwSpK7shDJ8s3kV8qMAdH0gB7v_sdUyjBPrL4otjMKzQOqMDKvE9Ce3ezfq_DQjhzEEmPHJYvEcYAVEkTTycpoAsSQ4c0tuXMnqsh2p5BwZPXzSyvGLiW3x4HPEPly6L-CkeljGpMeYs1nv9z41RZigbNQ79xQtcnn5oH9IFj1r9miGTo3yJScwyKAxn0NFntJaYxOp5fKmgTGp_Q1t2jVoNZA3wb0lnke9kyeOogVJSu6mzyyy5a3ChNuwXJH0zxBTflW8BG7vLZO2UF9n2HlpRqOxQLhR0yH3Pbb-ezZYxHnbsuL6gaBDgaNZT1mL8qBgGesqy11zOwx-fke58dY1huCVyqCI1_at7Lk4hjmwpxSpFfSBJYBod-_i5CxZub7BbXCjJ4kchIhDRvhGnrDQI7qklCGqJOY2dGQVqqicBmq-5f1WOAfuo0aCr4FpkYPZsyzZy8F2-sopcpRf8eQx8NoSWvwWsh7DZtv8_f-EYx6lmi1I-sC33I5mWCR-gbk3R8XeyNmjWaenyf-Z1V0kJTWn1wqAiv4jCNpE_hcBnqHTMvFXIKsVfDpRBqGrSXBJem3oUa8YK3ERQaw8B6d2TbmU1LRWBz1W9sjKefQC6QepbyRLPfqJabCQtqREXuJhw4j8MuNapnzJErhsnmMZbDAxgaDFZ85PRrnXGO6qJHHWgrbljDSGWqOCU5s6jNZbqvgZYUTYLhxTF1hzUzmPdMaVD0nIaRigBUIiD2nOjx4lldCc56fC8-WuGypCEJ9ReV5u-GSBnvZ6Se57Pib_S8vkBH6bA8cDgtaanLauAFOsjtR-uYeU27sFtf45GrKno4MDAU06jdNM4NwDPsKiTnhg_8Fjn9xCYPl6iT-3EzOAX-QqBJSea39--VvWl-SB9my7y349XO0JIqmoovlrRsUlSkwxEt5duvJ-Tg5f0trFztzREvp3_0qHyqoPS_D2k6lYYu5bXEZWAdT0sNtrTxIYZQPgxz7jtPIZ15ECnq2rH40xPVOw3dRN-cpUGNOB_Z8gmx2nfx7obyqeAHALmdSRpzwzH75QdbR49ALbpjercPlTxOh03CfRHDejZLwyON9IoxOVGcGIYDn7Z5zloR8IQd6wd8eQ7bo",
        "cookie_scmo.oree.com.ua": "SCMO_PROD_2|ZfrDY|Zfq2V",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # 'Cookie': 'lang=uk-UA; ASP.NET_SessionId=m31wppeh0k5d1pdnibzaz1rk; .AspNet.Cookies=Ziw5UIZ-ZFcD9xqR90RTgdlvcW7mc8FQ6sWCPvFzuYJYFen0z0dNTlDwDh9bp4yXKrLeVF5zs-ty3JNbIVAkMAdVdgwO25Zd5YhxMM3h94oYkaVDnFndl_LIDlm_HAP6q_0K28vWDfftNprJAZ70XXaJhQAYzgxTsF3QSQuJGEOzUIbXuCah7WtHi9mubTcxWDxfX_AOyYmAgCq9_6xSvjGWPhUtLIblbat_1yaqxy7S552aOiTjQNHg6Bpr7RHRLX8422Q4616x0odp8JyDv_bwzg8DHYHtXXTUUsavxvPY0Q2Ll45SaLdCFy7faxAAkxXt9hIJd1HVrUAVhC6CvuHBSjE3QbH3B5CH2izQvQOPMrVFzF-_2H9Z-k5p0sNcR32tXdD-bDP5OcJ1gRxQcsaIa8Oumw5AzKs0kscHVVwjtxGjcHdLaKI8ADeFQjtZlax1Z-jWjQrUNsYa4P4nZaOpapvfqf9YRxxRUVsdr108T2d4h_DRL25cKWmuzpsY5GrhsdY7uMuxqVpO8xTU2bqBJ4fc6nC55TcdpSZhXt8dON43auUX8Qys9DLnOC_Z_iqfSs7uD_ewTeW3Os8RT_S8XLxrpgXCR4JCy7LnJEjZlovu9e9Usu8RMMOBs-aD9H4ki1UyDI_9aR3Yi85Gz9avYpOMTg0J3cWBMCZjfcSWBbQaN1pvdgR_Nw3adzZraI87G8_731_7OxkYpn_sgWv8Om0QPoZ6ZIR5Weotx5nPhUqoITA5HtVbMe8h26X7N49jxfY-zNxrByXkrNHAeC6DTflVS54gIzFfvlndjhKSsNsGesmll2DQPM4RjjA_YKv2wTh9zbDHdItvzSoizacS8UawUfAiVp_l5ybJ32M0gKsKqXYKW_iQobyk9OF-ZxEcyubqLS2aUKPqjTOt_OPqRnwfQkytEyt5xH4GKO0ZReDEIyHIEukJRgB96-EP8ROXwfcHj3Cj-fbyTgvEEdfJwG1-GRzNHHTz9FpK0kycs58cyxe2Z1nsX_at14axprXNdYFnFdr-i3uDAlGGKqGIBBC5int8F3pxUkO-A7yDVBaDiWvSCV9BtfHTTDAW5mv5JfiWUs4m28h60K1QRroKpx3PK8TP4i_KZxq-xtmLzYnGURaODwHpH2Qysoy59dEAoXJqmY7LttCYYgVy8dKz1m7yi5-KeYRdoFalv17x5cdrlEyzYmWCFM2n2-9-2aKXUIxRRRKtC-eUQCqmpoJmEacHaZeilNOW_kQcADpFx6Pc_X1BVr2L7huomb3SEozD1rfjb1LDFTdfYYyi7zt-yQzRaS2kYXLto4jrMRi583sFXQd-sB16UJ6DZBnS_iaShCm2hGyOxWjss9Prikhmearw-Amqp4RkCCJ-Z8imz3S5zRzC6QVcp2EoidmMj_i4kxWGLkzhrYrtRI7BHG6pZi8cXsdKLfQkWQzCysR3Y_VbCIViM5sQCaraE50AtU1kqEiO6a7VKgP4Y7BTACOJK-6hOt4Mj_Y4NwSGReEJCzY-Lyu8fBN1NG-Y71YFpXyV20KcsTgOdu3RKcv8NmUo4wkAaRh04sNRXIKSfG_ZHWoclv5MbyZXq9P8XT350LONkBY59yfRhTG1qEfie0VN7UKv0LzMojT9vquk4GwmIPIFNpSnOAEpFy9eEP6ussAZBAwSpK7shDJ8s3kV8qMAdH0gB7v_sdUyjBPrL4otjMKzQOqMDKvE9Ce3ezfq_DQjhzEEmPHJYvEcYAVEkTTycpoAsSQ4c0tuXMnqsh2p5BwZPXzSyvGLiW3x4HPEPly6L-CkeljGpMeYs1nv9z41RZigbNQ79xQtcnn5oH9IFj1r9miGTo3yJScwyKAxn0NFntJaYxOp5fKmgTGp_Q1t2jVoNZA3wb0lnke9kyeOogVJSu6mzyyy5a3ChNuwXJH0zxBTflW8BG7vLZO2UF9n2HlpRqOxQLhR0yH3Pbb-ezZYxHnbsuL6gaBDgaNZT1mL8qBgGesqy11zOwx-fke58dY1huCVyqCI1_at7Lk4hjmwpxSpFfSBJYBod-_i5CxZub7BbXCjJ4kchIhDRvhGnrDQI7qklCGqJOY2dGQVqqicBmq-5f1WOAfuo0aCr4FpkYPZsyzZy8F2-sopcpRf8eQx8NoSWvwWsh7DZtv8_f-EYx6lmi1I-sC33I5mWCR-gbk3R8XeyNmjWaenyf-Z1V0kJTWn1wqAiv4jCNpE_hcBnqHTMvFXIKsVfDpRBqGrSXBJem3oUa8YK3ERQaw8B6d2TbmU1LRWBz1W9sjKefQC6QepbyRLPfqJabCQtqREXuJhw4j8MuNapnzJErhsnmMZbDAxgaDFZ85PRrnXGO6qJHHWgrbljDSGWqOCU5s6jNZbqvgZYUTYLhxTF1hzUzmPdMaVD0nIaRigBUIiD2nOjx4lldCc56fC8-WuGypCEJ9ReV5u-GSBnvZ6Se57Pib_S8vkBH6bA8cDgtaanLauAFOsjtR-uYeU27sFtf45GrKno4MDAU06jdNM4NwDPsKiTnhg_8Fjn9xCYPl6iT-3EzOAX-QqBJSea39--VvWl-SB9my7y349XO0JIqmoovlrRsUlSkwxEt5duvJ-Tg5f0trFztzREvp3_0qHyqoPS_D2k6lYYu5bXEZWAdT0sNtrTxIYZQPgxz7jtPIZ15ECnq2rH40xPVOw3dRN-cpUGNOB_Z8gmx2nfx7obyqeAHALmdSRpzwzH75QdbR49ALbpjercPlTxOh03CfRHDejZLwyON9IoxOVGcGIYDn7Z5zloR8IQd6wd8eQ7bo; cookie_scmo.oree.com.ua=SCMO_PROD_2|ZfrDY|Zfq2V',
        "Pragma": "no-cache",
        "Referer": "https://scmo.oree.com.ua/portal/default.aspx",
        "Sec-Fetch-Dest": "iframe",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0",
        "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Opera";v="108"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    params = {
        "boid": "1d46cedfa548472098a17510ba2f023e",
        "_dc": "1710932831658",
    }

    response = requests.get(
        "https://scmo.oree.com.ua/portal/Plugins/PXS/Pages/Intraday/Lightboard/Default.aspx",
        params=params,
        cookies=cookies,
        headers=headers,
        verify=False,
    )

    src = response.text
    # soup = BeautifulSoup(src, "lxml")
    # json_str = soup.find("input", attrs={"id": "lastTradeChartPoints"}).get("value")
    # # # Декодирование HTML-сущностей
    # decoded_json = html.unescape(json_str)

    # # # Преобразование декодированной строки в объект Python с помощью json.loads()
    # data_json = json.loads(decoded_json)

    # # for item in data_json:
    # #     print(f"Date: {item['Date']}, Price: {item['Price']}, Quantity: {item['Quantity']}")
    # formatted_data = [
    #     {"Date": item["Date"], "Price": item["Price"], "Quantity": item["Quantity"]}
    #     for item in data_json
    # ]
    #  # Получение текущего времени
    # now = datetime.now()

    # # Извлечение текущего часа
    # current_hour = now.hour
    # name_csv = f"{current_hour + 2}-{current_hour + 3}"
    # filename = os.path.join(json_path, f'{name_csv}.json')
    # # Сохраняем в файл
    # with open(filename, "w", encoding="utf-8") as f:
    #     json.dump(formatted_data, f, ensure_ascii=False, indent=4)

    # Получение текущего времени
    now = datetime.now()

    # Извлечение текущего часа
    current_hour = now.hour
    name_html = f"{current_hour + 2}-{current_hour + 3}"
    filename_html = os.path.join(html_path, f"{name_html}.html")
    with open(filename_html, "w", encoding="utf-8") as file:
        file.write(src)


def get_data():
    # Получение текущего времени
    now = datetime.now()

    # Извлечение текущего часа
    current_hour = now.hour
    name_html = f"{current_hour + 2}-{current_hour + 3}"
    filename_html = os.path.join(html_path, f"{name_html}.html")
    with open(filename_html, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")
    json_str = soup.find("input", attrs={"id": "lastTradeChartPoints"}).get("value")
    # # Декодирование HTML-сущностей
    decoded_json = html.unescape(json_str)

    # # Преобразование декодированной строки в объект Python с помощью json.loads()
    data_json = json.loads(decoded_json)

    # for item in data_json:
    #     print(f"Date: {item['Date']}, Price: {item['Price']}, Quantity: {item['Quantity']}")
    formatted_data = [
        {"Date": item["Date"], "Price": item["Price"], "Quantity": item["Quantity"]}
        for item in data_json
    ]
    name_json = f"{current_hour + 2}-{current_hour + 3}.json"
    filename = os.path.join(json_path, name_json)
    # Сохраняем в файл
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=4)


def run_at_specific_timee_ach_hour(target_minute, target_second):
    while True:
        now = datetime.now()
        target_time = now.replace(
            minute=target_minute, second=target_second, microsecond=0
        )

        # Если целевое время уже прошло, устанавливаем его на следующий час
        if target_time < now:
            target_time += timedelta(hours=1)

        print(f"Скрипт запланирован на {target_time}")

        # Ожидание до целевого времени
        while datetime.now() < target_time:
            time.sleep(
                1
            )  # Спим по 1 секунде, чтобы избежать чрезмерной загрузки процессора

        # Вызов функции после достижения целевого времени
        get_requests()

        # Планирование следующего запуска на следующий час
        time.sleep(10)  # Короткая пауза перед планированием следующего запуска

def json_to_csv():
    now = datetime.now()

    current_hour = now.hour
    name_json = f"{current_hour + 2}-{current_hour + 3}.json"
    filename = os.path.join(json_path, name_json)
    # Читаем данные из JSON файла
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    name_csv = f"{current_hour + 2}-{current_hour + 3}"
    filename_csv = os.path.join(current_directory, f"{name_csv}.csv")
    filename_xlsx = os.path.join(current_directory, f"{name_csv}.xlsx")
    # Открываем файл CSV для записи
    with open(filename_csv, 'w', newline='', encoding='utf-8') as csvfile:
        # Задаём названия колонок для CSV файла
        fieldnames = ["Дата", "Година", "Обсяги", "Ціна"]
        
        # Создаём объект DictWriter, указываем файл, заголовки и разделитель (если нужен другой, кроме запятой)
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',')
        
        # Записываем заголовки в файл
        writer.writeheader()
        
        # Проходим по каждому элементу в списке
        for item in data:
            # Разделяем дату и время
            dt_object = datetime.strptime(item["Date"], "%Y-%m-%dT%H:%M:%S")
            date = dt_object.strftime("%Y-%m-%d")
            time = dt_object.strftime("%H:%M:%S")
            
            # Записываем данные в строку файла
            writer.writerow(
                    {
                        "Дата": date,
                        "Година": time,
                        "Обсяги": item["Quantity"],
                        "Ціна": item["Price"],
                    }
                )
    data = pd.read_csv(filename_csv, encoding="utf-8")

    data.to_excel(filename_xlsx, index=False, engine="openpyxl")
        
# def jsons_to_csv():
#     folder = os.path.join(json_path, "*.json")

#     files_json = glob.glob(folder)
#     # Открываем файл CSV для записи
#     with open("data.csv", "w", newline="", encoding="utf-8") as csvfile:
#         # Задаём названия колонок для CSV файла
#         fieldnames = ["Дата", "Година", "Обсяги", "Ціна"]

#         # Создаём объект DictWriter, указываем файл, заголовки и разделитель (если нужен другой, кроме запятой)
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=",")

#         # Записываем заголовки в файл
#         writer.writeheader()
#         # Собираем все данные в один список
#         all_data = []
#         for item in files_json:
#             with open(item, "r", encoding="utf-8") as file:
#                 data = json.load(file)
#                 all_data.extend(
#                     data
#                 )  # Добавляем данные из текущего файла в общий список

#         # Сортируем список по дате
#         all_data_sorted = sorted(
#             all_data, key=lambda x: datetime.strptime(x["Date"], "%Y-%m-%dT%H:%M:%S")
#         )

#         # Теперь у вас есть отсортированный список all_data_sorted, и вы можете записать его в CSV
#         with open("sorted_data.csv", "w", encoding="utf-8", newline="") as f:
#             fieldnames = ["Дата", "Година", "Обсяги", "Ціна"]
#             writer = csv.DictWriter(f, fieldnames=fieldnames)
#             writer.writeheader()

#             for item in all_data_sorted:
#                 dt_object = datetime.strptime(item["Date"], "%Y-%m-%dT%H:%M:%S")
#                 date = dt_object.strftime("%Y-%m-%d")
#                 time = dt_object.strftime("%H:%M:%S")

#                 writer.writerow(
#                     {
#                         "Дата": date,
#                         "Година": time,
#                         "Обсяги": item["Quantity"],
#                         "Ціна": item["Price"],
#                     }
#                 )
#         # for item in files_json:
#         #     # Читаем данные из JSON файла
#         #     with open(item, "r", encoding="utf-8") as file:
#         #         data = json.load(file)

#         #         # Проходим по каждому элементу в списке
#         #         for item in data:
#         #             # Разделяем дату и время
#         #             dt_object = datetime.strptime(item["Date"], "%Y-%m-%dT%H:%M:%S")
#         #             date = dt_object.strftime("%Y-%m-%d")
#         #             time = dt_object.strftime("%H:%M:%S")

#         #             # Записываем данные в строку файла
#         #             writer.writerow(
#         #                 {
#         #                     "Дата": date,
#         #                     "Година": time,
#         #                     "Обсяги": item["Quantity"],
#         #                     "Ціна": item["Price"],
#         #                 }
#         #             )
#     # Загрузка данных из файла CSV
#     data = pd.read_csv("sorted_data.csv", encoding="utf-8")

#     # Сохранение данных в файл XLSX
#     data.to_excel(f"sorted_data.xlsx", index=False, engine="openpyxl")


# if __name__ == "__main__":
#     run_at_specific_time(59, 30)

def run_at_specific_time(target_time_str):
    # Преобразование строки времени в объект datetime сегодняшнего дня
    now = datetime.now()
    target_time = datetime.strptime(target_time_str, "%H:%M:%S").replace(year=now.year, month=now.month, day=now.day)

    # Если целевое время уже прошло сегодня, устанавливаем его на следующий день
    if target_time < now:
        target_time += timedelta(days=1)
    
    print(f"Скрипт запланирован на {target_time}")

    # Ожидание до целевого времени
    while datetime.now() < target_time:
        time.sleep(1)  # Спим по 1 секунде, чтобы избежать чрезмерной загрузки процессора
    
    # Вызов функции после достижения целевого времени
    get_requests()
    get_data()
    json_to_csv()

if __name__ == "__main__":
    # run_at_specific_time("15:50:50")
    run_at_specific_time("16:03:00")



# if __name__ == "__main__":
#     creative_folders()
#     get_requests()
#     get_data()
#     json_to_csv()
#     # run_at_specific_time("13:59:50")
