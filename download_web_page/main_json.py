import json
import time
from pathlib import Path

import pandas as pd
import requests

current_directory = Path.cwd()
json_directory = current_directory / "json"

all_data = [
    "856b3e74-1725-4e47-b36d-0216d1e6de42",
    "045b43d0-9246-430a-8bc7-8c489ad82381",
    "c00ac365-f0d0-46f4-b561-6cb0a805d856",
    "66e42fb9-8faa-44dc-b133-fc9dc158c1b8",
    "007f5d23-ce51-4b76-8a83-b1c43a2e34d6",
    "145780aa-948f-4d53-a9c6-d14ec131c133",
    "f5f98a44-cf6d-48ce-bc73-c50d00291ad9",
    "cd947a04-2b67-4658-9ae8-85d2db93bb25",
    "88b3a447-612c-4155-a48d-2f26f37619b1",
    "582289d6-4d39-44cb-a2ab-97b02540135e",
    "8c2d3765-35f8-4f0e-9fc8-b7309fd13fb3",
    "7d367b8c-8ffc-4647-9b1d-68691e73ba27",
    "29161cf7-a5f2-4e1a-812d-f598652bef46",
    "0df1fa9f-2f44-4646-8680-bf49983b9800",
    "6eee75e6-809d-49b7-a51e-82d9b22d7fbf",
    "36a36885-3486-4ee1-9826-888079e0caa9",
    "dd2bf428-a65e-44e0-ba3d-d5bf4cb5c569",
    "1e7514cc-9830-498c-b727-d0dc3f5ca4c2",
    "348ee66e-600c-4f64-a318-817958c58fa4",
    "d7d5d5b1-9041-4cb3-a058-f403f1800a0a",
    "487b0e8a-3522-45e0-a9df-66235bae0288",
    "4c07465b-f968-4425-a23f-60811ad52d86",
    "5872d4dd-3588-4bc3-90bc-d5dc948a252b",
    "b7931ffd-e61c-4ac3-8c95-4556c73680d3",
    "0faa6a2b-d2f2-4a88-b91e-5f119dfc907e",
    "f9161ae1-4040-4b4d-9124-fc8fff817616",
    "b91a9a02-7d45-4486-941d-94929c857bf1",
    "f031e281-a9f0-4273-8add-e948684d3769",
    "3e098eac-a09f-4e38-8efd-56cc4bc3f602",
    "581a7db2-b105-45e8-b3c2-639b78dbf9ab",
    "410f7ab5-dcf4-4ae7-8e70-c18c53b2bca4",
    "a3a062c3-875e-4852-9ac8-bedce6f1360a",
    "f5747003-3096-422e-a5d3-ae9989695ed5",
    "9dd41e8b-f02e-46dd-9c32-eb3cdee2dd9c",
    "ae447dad-d592-4ea7-a755-74595051e924",
    "786a2b87-c9eb-424b-8260-0045330841ce",
    "852a47bb-3b05-451c-8266-05176ad3bade",
    "cabe6332-a86a-416d-846a-c8d6e69a7da1",
    "46cd14c4-a167-4ef1-bef6-817308c114a9",
    "c6bbc69f-5c88-4a09-b453-13c43f365123",
    "e5cd1fa3-349b-4518-af3f-7dccce86d93d",
    "c36d2b7e-5add-4b9e-a85d-bf51e6b4eb37",
    "16760ffc-f793-4487-9866-b6b4480868ca",
    "01737266-71fe-4c74-ac01-75ebea0b27e6",
    "4ace3f41-7b48-4e1e-85b0-823d6e27a808",
    "74fe6222-b6a2-4e8b-8f6c-1616af1c3244",
    "e51993b2-28f4-4178-98de-cc9778076ad0",
    "398c2822-9b88-49b2-abaa-8105a5e05d39",
    "a5c55128-a227-4a42-b71c-84bb007d26f6",
    "24a47dea-ea22-41b8-9413-c9cdf8a9e196",
    "22b47795-de65-4293-8d21-3c7b74c4beb9",
    "72c51005-c772-43b3-ada6-e0b0cb003399",
    "3cf72396-45c3-456b-8eb9-ee70e6915e47",
    "ca62ac37-b7ab-4917-9f1e-8e461cf06808",
    "14136f9a-e7ee-4963-9265-b104393e22c4",
    "25eb97a1-7e63-4b67-9f45-8845cc1e3959",
    "7cd37cc4-7665-44e9-b4d6-e0c1fdccdc8f",
    "4cb7d289-c3cd-4f38-a42a-68ba3129311a",
    "41ef27ac-b9fb-421b-8a46-3df1a1cf8f88",
    "b0255414-1eaa-4a96-afef-bb03dbeadfe7",
    "3271a06a-f8b3-440d-aadc-79596f9b2aa0",
    "e2410d55-e69f-484c-aceb-5fcb2065d6df",
    "817a9f11-87e6-428d-b70e-31d6a439b5a0",
    "c24487d9-f604-4d37-896b-d15c9314f145",
    "be3e4029-385a-4d83-a6a8-64326d4adf48",
    "e81e70fb-8044-4246-a429-12e2aa6c43fc",
    "bd116c90-b3cb-4eeb-a8db-90c3922b90f4",
    "4d63ff21-b759-40d3-a00e-c6ed6f38a4a4",
    "41329723-6b38-409b-848f-ff1ad2e1a1f0",
    "05348828-3491-416c-9442-83961b77115b",
    "7f980e4b-5407-4a7e-9531-f363fb5e1e7b",
    "33e9f487-4aa1-4c7e-8ef1-02e413bae2e5",
    "1620f956-93f6-4636-b033-240f6a8b6d4c",
    "58a2194e-3039-46aa-a4e0-56b89207f164",
    "fb5d94cc-01b3-4fbf-b39d-efd6f6bcf6ed",
    "529703d8-6cc2-4f40-8c08-31a76d7ed8e4",
    "7293a517-6a75-4061-bd4d-e5414a056f21",
    "73853897-60fa-4d59-9c9c-77e4267c769e",
    "91215a35-fe5e-4301-83b8-8dfc23e197e0",
    "379450c9-740a-4907-b505-45bc5d21f47b",
    "e60db04f-e712-45cc-a5e0-22131c367d04",
    "b677bd09-bc08-4be5-a941-2639919e99dd",
    "ce7442d5-bbf2-4240-8e2c-502725233f58",
    "a728ac2b-749e-4eb8-b19d-53b19d6bb7de",
    "8bf1ce2f-40f4-4b5a-a9b4-d230b84fd0e6",
    "9c278e99-e861-46db-be0a-3c24388694bf",
    "3e985a6e-4165-40ed-a1e1-4e1f4d5762b2",
    "62423518-ef70-47a7-a2ad-5c65bc3756e8",
    "4b64bfb2-4fc9-4826-9ebb-f4c99f55b6b1",
    "fbf79846-6bba-460d-91bf-4924a84e4c8f",
    "3f81e803-fa1b-4799-a55d-bad4e5ab3ebc",
    "af0dbb80-abcd-45e3-8fbc-a2cd62f8e2a1",
    "c509bdbb-d717-4365-b4c6-11fc000574ca",
    "943a9e94-43ed-44de-abfc-8bc44fd7ac33",
    "236ccafe-7f70-4bfd-802b-81278604939f",
    "4ba41c53-6a5c-4ad7-8bf6-4266bc3083c9",
    "152e29a2-4b5e-473f-9cf8-64da5c08706e",
    "7303f887-d224-443b-8b3a-f85226574dcd",
    "8d9467e9-68ff-49ff-9877-4427a52a1095",
    "74217c09-0a15-4b69-af2f-361ed0038b71",
    "32ebd6d9-fd44-4a86-9997-683dbf3530b1",
    "bc993b63-ac65-40e6-b839-6c3e827b2275",
    "02f0a752-080b-413f-aebc-8e648e21c49d",
    "6aeaa5bb-c629-431c-9985-d396659bfd05",
    "abae46b0-826b-4e33-af3e-427caa57293b",
    "497dea19-51a6-46ea-bb68-1c9dc627ab9a",
    "a650db74-b3fb-4342-af98-4a920c208add",
    "569a9a4f-39da-4169-9ffc-9623582e9f5c",
    "51ae4b2e-aeff-42a5-a374-60d410997fb4",
    "8e9f247b-84a3-4933-a64a-9308832cab82",
]
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
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
        print(data)
        time.sleep(10)
    else:
        print(response.status_code)

# def extract_user_name(user_id, user_options):
#     filtered_user = list(filter(lambda x: x["value"] == user_id, user_options))
#     return filtered_user[0]["text"] if filtered_user else None


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
