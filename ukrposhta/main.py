import json
import os
import time
from pathlib import Path

import pandas as pd
import requests
from loguru import logger

current_directory = Path.cwd()
json_directory = current_directory / "json"
json_directory.mkdir(parents=True, exist_ok=True)
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"

logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {line} - {message}",
    level="DEBUG",
    encoding="utf-8",
)


def get_html_values_list():
    cookies = {
        "cookie_notification": "1",
        "cookie_notification": "1",
        "_cfuvid": "DkgqyO42sHDJksp5JCvKofCEl2uIKXIuwD64LofIYgc-1738427908130-0.0.1.1-604800000",
        "cf_clearance": "Qfl5.Tkgdidfs0Wj8XcNBBGoVc4bgZXIoWp5EAGzC2Q-1738427908-1.2.1.1-Uhjw1dzJ0L.nGPERG.gMafxQZ6urU4M.phZYW8NojCPrTcikHq6YNBCQPC4HGqVY5HP4QjFH7UsX7goPVL1MpoZP9gFensMkLkfR9ulkQz0J0WMoYR0qKMmX2XIiRI7JALcmPUR_MHC0eNnhBps.Jtf124_sALlqwUbWyCeOu2h8olEnSixT2TDp8YGjCEL8jbKorYoxSFTzOYUpeZJQDpr1XFpVhTW9a67oZBrTF2AtYeEOsq6mYnCZlxxMyeQodEkWv53xc0QeXtMlAENV9dUeuGXMAClFRg56AWdoSH4",
        "salt": "fc04658a",
        "TS011fabd3030": "01e5a50318f88c455208cc934bb293277e28de5b77c69e741a4b5b603c3a430dff897ee7329fd92a2ae412cf000bc6f631de233b14",
        "usrcheckvr": "undefined",
        "packageType856b3e74-1725-4e47-b36d-0216d1e6de42": "PRIME",
        "international_isShowLast20": "false",
        "packageType045b43d0-9246-430a-8bc7-8c489ad82381": "PRIME",
        "internationalgroupfc04658a": "045b43d0-9246-430a-8bc7-8c489ad82381",
        "XSRF-TOKEN": "eyJpdiI6Ild6MTZWeU8yTWVibWhDaWlHVFwvSFdBPT0iLCJ2YWx1ZSI6ImprdXNBRmx1VUVTVUtPTUM3MEh5c2hPeXdzRlwveHZuUUk2YjlvbE5JeW13QXJhcWxtZ3pYXC8xTExcLzh3YVwvNkFSIiwibWFjIjoiOTU3MTI3NWI1ZDA1ZDRjOWJjNmMyM2NmODUyNGZjOTc1Yjk2ZDg4YjVlMWU4OTY5MTc4YWQ3OGE1YTgxMDNmMiJ9",
        "laravel_session": "eyJpdiI6Ik1wOEtcL0lWYnk5cEJ4THNcL256dVVZdz09IiwidmFsdWUiOiJEbXczS2Z5N2g4UlwvbCt4VVdCcW5QY0F0NWpKVVFGZG13enh3bmRleVJGVGx5emorN3Z4d2R5VklOQWdDZVdJTiIsIm1hYyI6ImNmYTg3NjU0YWU2N2IwYzAwMTA0YjVlMWJmNWI5ZWIwOGVmMDRlMDI5MDA1NzBkN2YyMzE3ZDhkODIyZTUwNGEifQ%3D%3D",
        "__cf_bm": "44N45axiU6qJpS1lB07mdS.RnXFHkUR_w7dlEvxFAV4-1738488310-1.0.1.1-DI73Ke3iFQQ__Qh6vQuRXnOkEezfC_di3jrF6Nahdu2mVehw1LdF21Su5NAD927UkrwrBi0cPh6pHE4FiMvhlw",
        "TS011fabd3": "013ec6202eb6dc97010b94ee0bd0ce79dfcc739ecc3a55a5c5049edd39a4a865d0d3d625977c0b4d2027fcb5da4991f9022a581994763635c9517959b9bbf8e0cc7379df18a6949ba82ae30e65ad9517ee9b9cf2507fd5c6ff5f96e396470ce64d67458b96",
        "TSf3258379027": "085f5781a8ab20000d0709d3cb5374aea35ef5690581f4006a2ef968cb1269b3f46e657a65df0e76087f64e95e11300029515fae00f56b0108f6eebbd524b3818c0deae0f73a865ecde753d88a580b48e0738a9f261a1b567c382adbbda7e889",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "DNT": "1",
        "Referer": "https://ok.ukrposhta.ua/ua/lk/welcome-page",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    response = requests.get(
        "https://ok.ukrposhta.ua/ua/lk/international",
        cookies=cookies,
        headers=headers,
        timeout=30,
    )
    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open("youcontrol.html", "w", encoding="utf-8") as f:
            f.write(response.text)
    logger.info(response.status_code)


def get_json():
    cookies = {
        "__cf_bm": "bMzSAjOb3sOLVVWO.xepfVg_D8UuJ0UVwySfuB8O24U-1738427908-1.0.1.1-CXEFPUA6eLqugiEEZQRKF05uRbdJ.0pYLlayayTV1foBIPDaI6bRM_kzt3RbPSl2xaHuSFBvm466WVCCJL9ujg",
        "_cfuvid": "DkgqyO42sHDJksp5JCvKofCEl2uIKXIuwD64LofIYgc-1738427908130-0.0.1.1-604800000",
        "cf_clearance": "Qfl5.Tkgdidfs0Wj8XcNBBGoVc4bgZXIoWp5EAGzC2Q-1738427908-1.2.1.1-Uhjw1dzJ0L.nGPERG.gMafxQZ6urU4M.phZYW8NojCPrTcikHq6YNBCQPC4HGqVY5HP4QjFH7UsX7goPVL1MpoZP9gFensMkLkfR9ulkQz0J0WMoYR0qKMmX2XIiRI7JALcmPUR_MHC0eNnhBps.Jtf124_sALlqwUbWyCeOu2h8olEnSixT2TDp8YGjCEL8jbKorYoxSFTzOYUpeZJQDpr1XFpVhTW9a67oZBrTF2AtYeEOsq6mYnCZlxxMyeQodEkWv53xc0QeXtMlAENV9dUeuGXMAClFRg56AWdoSH4",
        "salt": "fc04658a",
        "TS011fabd3030": "01e5a50318f88c455208cc934bb293277e28de5b77c69e741a4b5b603c3a430dff897ee7329fd92a2ae412cf000bc6f631de233b14",
        "usrcheckvr": "undefined",
        "packageType856b3e74-1725-4e47-b36d-0216d1e6de42": "PRIME",
        "international_isShowLast20": "false",
        "packageType045b43d0-9246-430a-8bc7-8c489ad82381": "PRIME",
        "XSRF-TOKEN": "eyJpdiI6IjFnU2tkWWY1ditKUlpPK25EbHpXZ1E9PSIsInZhbHVlIjoiaHBYRkp0ZWhmZ2JvUjlNMkJOUTdPSU8wN1JteklFY0tpUHd4djRkd1dFdHZMS1BHY2NnWjlLUFhUc2tid1RTbSIsIm1hYyI6IjdlNTQwMWI5NzgwNWE5M2M3ZTViZTZjNjI4MzFlNjUwMTE2NWZjN2Q0OWVhNGRjMGU3MmI5Y2ZkMzk4M2I3YWQifQ%3D%3D",
        "laravel_session": "eyJpdiI6IittT1VqKzdwaStuUFNtWHg3YjE1UUE9PSIsInZhbHVlIjoiSVNwZjZGOXppQUtpVnprVjRsKyt0dmpCOXVWT2JKQkpreXZOOWhUVksrNUtaTmtpdk9lSEU1Y0xqMEVPRThtbSIsIm1hYyI6ImUzNWZiYTAyNjFhZjBhYzY4NjM2ODdjMGQ3Mjg0MjE2N2YwZjU4OTY0NTQzMTMyMDQ1NDIxZWFlZTJkNzIwNzEifQ%3D%3D",
        "TS011fabd3": "013ec6202e38cfeca374b4b35d56307fd772ce54fc6095558760127b20cc3af2d0bcc973f73803e35a63af66f1b971025bdefa5e0781f7a4efc0b3667fc802c1153c2f7b5239d06091a843eb1bb8be308575f0b5370f570ca68c8dc360b2820ba4ec0f4b57",
        "TSf3258379027": "085f5781a8ab2000614e55bbf8e83df1af7dc7c3fa3b76e2d47ba395306b059d0a8a0e83eaacb21f08686c0591113000337bbb05e30ecc02a33270d1e945bf5b238045f12d8f3b7ebfe6744989956a76376ac1856f04e01de96dfdefd65a47dd",
        "internationalgroupfc04658a": "856b3e74-1725-4e47-b36d-0216d1e6de42",
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "DNT": "1",
        "Origin": "https://ok.ukrposhta.ua",
        "Referer": "https://ok.ukrposhta.ua/ua/lk/international",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "X-XSRF-TOKEN": "eyJpdiI6IjFnU2tkWWY1ditKUlpPK25EbHpXZ1E9PSIsInZhbHVlIjoiaHBYRkp0ZWhmZ2JvUjlNMkJOUTdPSU8wN1JteklFY0tpUHd4djRkd1dFdHZMS1BHY2NnWjlLUFhUc2tid1RTbSIsIm1hYyI6IjdlNTQwMWI5NzgwNWE5M2M3ZTViZTZjNjI4MzFlNjUwMTE2NWZjN2Q0OWVhNGRjMGU3MmI5Y2ZkMzk4M2I3YWQifQ==",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    for data in all_data:
        json_data = {
            "method": "getList",
            "shipmentGroup": data,
        }

        response = requests.post(
            "https://ok.ukrposhta.ua/ajax/lk-api",
            cookies=cookies,
            headers=headers,
            json=json_data,
            timeout=30,
        )
        # Проверка успешности запроса
        if response.status_code == 200:
            json_data = response.json()
            with open(f"{data}.json", "w", encoding="utf-8") as f:
                json.dump(
                    json_data, f, ensure_ascii=False, indent=4
                )  # Записываем в файл
            print(data)
            time.sleep(10)
        else:
            print(response.status_code)


def process_data(data):
    user_options = data.get("response", [])
    all_data = []

    for item in user_options:
        try:
            recipient = item.get("recipient", {})
            addresses = recipient.get("addresses", [])

            detailedInfo = None
            if addresses:  # Check if addresses list is not empty
                address = addresses[0].get("address", {})
                detailedInfo = address.get("detailedInfo")

            recipient_name = recipient.get("name")
            recipient_phoneNumber = recipient.get("phoneNumber")
            barcode = item.get("barcode")
            lastModified = item.get("lastModified")
            weight = item.get("weight")
            deliveryPrice = item.get("deliveryPrice")
            all_data.append(
                {
                    "detailedInfo": detailedInfo,
                    "recipient_name": recipient_name,
                    "recipient_phoneNumber": recipient_phoneNumber,
                    "barcode": barcode,
                    "lastModified": lastModified,
                    "weight": weight,
                    "deliveryPrice": deliveryPrice,
                }
            )
        except (KeyError, IndexError) as e:
            print(f"Ошибка обработки записи: {e}")

    return all_data


# Пройтись по каждому JSON файлу в папке
result = []
for json_file in json_directory.glob("*.json"):
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    # Use the function to process data
    items_from_file = process_data(data)
    result.extend(items_from_file)  # Add all items from the file to result

print(len(result))
# Convert result list to DataFrame
df = pd.DataFrame(result)

# Sort DataFrame by 'lastModified' column in descending order (newest to oldest)
df = df.sort_values(by="lastModified", ascending=False)

# Save sorted DataFrame to Excel
excel_file_path = current_directory / "output.xlsx"
df.to_excel(excel_file_path, index=False)

print(f"Data successfully written to {excel_file_path}")
