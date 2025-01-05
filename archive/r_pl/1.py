import requests
import json
cookies = {
    'liczbaPokoi': '1',
    'dowolnaLiczbaPokoi': 'false',
    'rodzinneTooltip': 'true',
    '_cq_duid': '1.1710003251.1eYTMkRadkyuf5zf',
    '_cq_suid': '1.1710003251.AGqPfFPUXcIQqflQ',
    'KlientIdSchowek': 'ab475271-280b-4a51-91e5-95d97278c547',
    'cto_h2h': 'A',
    '_gcl_au': '1.1.2131582685.1710003942',
    '_ga': 'GA1.1.999934960.1710003942',
    '__cmpcpc': '__52_54_51_53__',
    '__rtbh.lid': '%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22FBuGAG6GpIioDmTOW2TX%22%7D',
    'smuuid': '18e242d72fd-947e6411b6bf-dd5b5cae-8e8f2749-5102a746-1225f232db2e',
    '_fbp': 'fb.1.1710003942210.2026858919',
    'FPAU': '1.1.2131582685.1710003942',
    'smPopupFormShowOnVisitCnt': '29',
    'BHTGuid': '9e5f1ced-4a52-4a55-a0aa-efbcbf689d11',
    '_hjSessionUser_1823437': 'eyJpZCI6ImYwMmQ0YTE0LTI2MjQtNWQxZS1iYTFhLWNiZDdiNjU5NTJiOCIsImNyZWF0ZWQiOjE3MTAwMDQwMTAxMDksImV4aXN0aW5nIjp0cnVlfQ==',
    '_smvs': 'DIRECT',
    'smOTimePopCap': 'popupForm:1710098780741|',
    '_uetsid': '42e69360de3711eeae64770bd2e2a3d3',
    '_uetvid': '42e68120de3711ee98d223df9814c583',
    '_clck': '1un0u0h%7C2%7Cfjz%7C0%7C1529',
    '_ga_HQWQ6ZSR4S': 'GS1.1.1710138051.5.1.1710138051.0.0.0',
    'wiek': '%5B%221994-01-01T10%3A00%3A00.000Z%22%2C%221994-01-01T10%3A00%3A00.000Z%22%5D',
    'RABTests': 'eyJ0ZXN0cyI6W3sibmFtZSI6InJvZCIsImRldmljZXMiOlsiRCIsIk0iLCJUIl0sInBhZ2VzVHlwZXMiOlsic3p1a2FqIl0sInBhdGhQYXR0ZXJuIjpudWxsLCJ2YWx1ZSI6Im5pZSJ9XX0=',
    'smvr': 'eyJ2aXNpdHMiOjQsInZpZXdzIjo1NiwidHMiOjE3MTAxNTA5MzUwNzYsImlzTmV3U2Vzc2lvbiI6ZmFsc2V9',
    'smOViewsPopCap': 'views:56|',
    'smPopupFormVisitCnt': '28',
    'cto_bundle': 'Olx6jl91YXdBWHpoWklGc0ZBbzRicmsyczRhYmFYMiUyQkREQ24xJTJGczRvT05Sd05JMkVSeXJqOGdiWGVlaGhCM0tHMDNnV1h3UjVKME9HS2czOGslMkJUTHlNVFV0YkhZNzRzclNFUlpDMTlIaFhWMnFjMUM3QzlHclFRMlBKNDBoM284SnZJaE5JajFYaFhNUk55UDVoMTV3aktWN3clM0QlM0Q',
    '_clsk': 'zrtk2w%7C1710152881395%7C1%7C1%7Cw.clarity.ms%2Fcollect',
    '_ga_HQWQ6ZSR4S': 'GS1.1.1710143132.6.1.1710152885.0.0.0',
}

headers = {
    'authority': 'r.pl',
    'accept': 'application/json',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'content-type': 'application/json',
    # 'cookie': 'liczbaPokoi=1; dowolnaLiczbaPokoi=false; rodzinneTooltip=true; _cq_duid=1.1710003251.1eYTMkRadkyuf5zf; _cq_suid=1.1710003251.AGqPfFPUXcIQqflQ; KlientIdSchowek=ab475271-280b-4a51-91e5-95d97278c547; cto_h2h=A; _gcl_au=1.1.2131582685.1710003942; _ga=GA1.1.999934960.1710003942; __cmpcpc=__52_54_51_53__; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22FBuGAG6GpIioDmTOW2TX%22%7D; smuuid=18e242d72fd-947e6411b6bf-dd5b5cae-8e8f2749-5102a746-1225f232db2e; _fbp=fb.1.1710003942210.2026858919; FPAU=1.1.2131582685.1710003942; smPopupFormShowOnVisitCnt=29; BHTGuid=9e5f1ced-4a52-4a55-a0aa-efbcbf689d11; _hjSessionUser_1823437=eyJpZCI6ImYwMmQ0YTE0LTI2MjQtNWQxZS1iYTFhLWNiZDdiNjU5NTJiOCIsImNyZWF0ZWQiOjE3MTAwMDQwMTAxMDksImV4aXN0aW5nIjp0cnVlfQ==; _smvs=DIRECT; smOTimePopCap=popupForm:1710098780741|; _uetsid=42e69360de3711eeae64770bd2e2a3d3; _uetvid=42e68120de3711ee98d223df9814c583; _clck=1un0u0h%7C2%7Cfjz%7C0%7C1529; _ga_HQWQ6ZSR4S=GS1.1.1710138051.5.1.1710138051.0.0.0; wiek=%5B%221994-01-01T10%3A00%3A00.000Z%22%2C%221994-01-01T10%3A00%3A00.000Z%22%5D; RABTests=eyJ0ZXN0cyI6W3sibmFtZSI6InJvZCIsImRldmljZXMiOlsiRCIsIk0iLCJUIl0sInBhZ2VzVHlwZXMiOlsic3p1a2FqIl0sInBhdGhQYXR0ZXJuIjpudWxsLCJ2YWx1ZSI6Im5pZSJ9XX0=; smvr=eyJ2aXNpdHMiOjQsInZpZXdzIjo1NiwidHMiOjE3MTAxNTA5MzUwNzYsImlzTmV3U2Vzc2lvbiI6ZmFsc2V9; smOViewsPopCap=views:56|; smPopupFormVisitCnt=28; cto_bundle=Olx6jl91YXdBWHpoWklGc0ZBbzRicmsyczRhYmFYMiUyQkREQ24xJTJGczRvT05Sd05JMkVSeXJqOGdiWGVlaGhCM0tHMDNnV1h3UjVKME9HS2czOGslMkJUTHlNVFV0YkhZNzRzclNFUlpDMTlIaFhWMnFjMUM3QzlHclFRMlBKNDBoM284SnZJaE5JajFYaFhNUk55UDVoMTV3aktWN3clM0QlM0Q; _clsk=zrtk2w%7C1710152881395%7C1%7C1%7Cw.clarity.ms%2Fcollect; _ga_HQWQ6ZSR4S=GS1.1.1710143132.6.1.1710152885.0.0.0',
    'dnt': '1',
    'origin': 'https://r.pl',
    'referer': 'https://r.pl/hurghada-wypoczynek/lemon-and-soul-makadi?data=2024-06-27&dlugoscPobytu=8&iataWyjazdu=WRO&liczbaPokoi=1&wiek=1994-01-01&wiek=1994-01-01&wybranePokoje={%221%22:1}&wyzywienie=all-inclusive',
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'x-source': 'r.pl',
}

json_data = {
    'HotelUrl': 'lemon-and-soul-makadi',
    'ProduktUrl': 'hurghada-wypoczynek',
    'LiczbaPokoi': 1,
    'Dlugosc': 8,
    'TerminWyjazdu': '2024-04-04',
    'Iata': 'GDN',
    'DatyUrodzenia': [
        '1994-01-01',
        '1994-01-01',
    ],
    'Wyzywienie': 'all-inclusive',
    'CzyV2': True,
}

response = requests.post('https://r.pl/api/wyszukiwarka/wyszukaj-kalkulator', cookies=cookies, headers=headers, json=json_data)

json_data_r = response.json()
with open('lemon.json', "w", encoding="utf-8") as f:
                    json.dump(
                        json_data_r, f, ensure_ascii=False, indent=4
                    )  # Записываем в файл