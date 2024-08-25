import requests
import json
from configuration.logger_setup import logger

cookies = {
    "_uid": "172406750548113",
    "device_view": "full",
    "cookiePolicy": "%7B%22accepted%22%3Atrue%2C%22technical%22%3Atrue%2C%22statistics%22%3A%22true%22%2C%22marketing%22%3A%22true%22%2C%22expire%22%3A1755603507%7D",
}

headers = {
    "Accept": "*/*",
    "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "Authorization": "",
    "Connection": "keep-alive",
    # 'Cookie': '_uid=172406750548113; device_view=full; cookiePolicy=%7B%22accepted%22%3Atrue%2C%22technical%22%3Atrue%2C%22statistics%22%3A%22true%22%2C%22marketing%22%3A%22true%22%2C%22expire%22%3A1755603507%7D',
    "DNT": "1",
    "Origin": "https://abw.by",
    "Referer": "https://abw.by/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


def get_html():
    cookies = {
        "TS01c18f0b": "01090ee16e65516184d6433261e0582c3057d2ee5318e4ef43c9eb320fecf649fa78ff5ee73e7d816e38db52669d3e7e1a29f34dfd",
        "JSESSIONID": "jNSJLlzh5-BDFasWJaHSv5uj01I8kxj7Kp7VrguD.rain7jb4",
        "TS0138fb12": "01090ee16e2b97f984c91ac91a8d12db24e519f096d244eab16564ff96d543a40f2169041479bd4157730144b2cd824265b0f58356",
        "TSPD_101": "08553781f9ab2800cd6d89cfac29b8c066b1d838609caccd347e8d1aed0c90dfa2db27d1eb3ca1e3e9b5b658415393e508efafdd8f051800e5ea8398a732861dd6aab69f9ec042d02595c50eb6132b0a",
        "TS0fb58479077": "08553781f9ab280004b8ba9733fce7e2665ea667ae2938dccf5f85370264142097b6b1bc6e62d11f52cf12c2fdcdde650839ca6bbe172000f1ea20996bbf6d8d3326698eb94c3e11894fce58ea7b0d028d508cf11f293b36",
        "TS0fb58479029": "08553781f9ab2800339c92767fd1a8c3e0e106c87f172b7094e1e98a5c4bdb22e3ad1158c5bf30bed4eb957bd5bd754c",
        "TSce795e2f027": "08553781f9ab2000ad0320b78d07045c8e3017eec48d80503e5ca3fe9751575f9a804e6cf7861a5c08a3e2cb1e1130001bad5a63cdab068fe6dfb29195a2c3b70381459a4b94d8fc60087472f68fca38400bae12f74f03124357366d7cbb3495",
    }

    headers = {
        "Accept": "application/xml, text/xml, */*; q=0.01",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        # 'Cookie': 'TS01c18f0b=01090ee16e65516184d6433261e0582c3057d2ee5318e4ef43c9eb320fecf649fa78ff5ee73e7d816e38db52669d3e7e1a29f34dfd; JSESSIONID=jNSJLlzh5-BDFasWJaHSv5uj01I8kxj7Kp7VrguD.rain7jb4; TS0138fb12=01090ee16e2b97f984c91ac91a8d12db24e519f096d244eab16564ff96d543a40f2169041479bd4157730144b2cd824265b0f58356; TSPD_101=08553781f9ab2800cd6d89cfac29b8c066b1d838609caccd347e8d1aed0c90dfa2db27d1eb3ca1e3e9b5b658415393e508efafdd8f051800e5ea8398a732861dd6aab69f9ec042d02595c50eb6132b0a; TS0fb58479077=08553781f9ab280004b8ba9733fce7e2665ea667ae2938dccf5f85370264142097b6b1bc6e62d11f52cf12c2fdcdde650839ca6bbe172000f1ea20996bbf6d8d3326698eb94c3e11894fce58ea7b0d028d508cf11f293b36; TS0fb58479029=08553781f9ab2800339c92767fd1a8c3e0e106c87f172b7094e1e98a5c4bdb22e3ad1158c5bf30bed4eb957bd5bd754c; TSce795e2f027=08553781f9ab2000ad0320b78d07045c8e3017eec48d80503e5ca3fe9751575f9a804e6cf7861a5c08a3e2cb1e1130001bad5a63cdab068fe6dfb29195a2c3b70381459a4b94d8fc60087472f68fca38400bae12f74f03124357366d7cbb3495',
        "DNT": "1",
        "Origin": "https://startup.registroimprese.it",
        "Referer": "https://startup.registroimprese.it/isin/search?0",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Wicket-Ajax": "true",
        "Wicket-Ajax-BaseURL": "search?0",
        "Wicket-FocusedElementId": "id59",
        "X-Requested-With": "XMLHttpRequest",
        "X-Security-Request": "required",
        "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    data = {
        "parolaChiaveFld": "",
        "denominazioneFld:contenitore:supplierSel": "",
        "regionFld:contenitore:supplierSel": "",
        "pvFld:contenitore:supplierSel": "",
        "classeProduzioneFld:contenitore:supplierSel": "",
        "classeAddettiFld:contenitore:supplierSel": "",
        "classeCapitaleFld:contenitore:supplierSel": "",
        "fldStartDtCostituzioneRi": "25/01/2024",
        "fldEndDtCostituzioneRi": "",
        "finanziamentoStartFld": "",
        "finanziamentoEndFld": "",
        "codiceAtecoFld:contenitore:supplierSel": "",
        "hashtagFld:contenitore:supplierSel": "",
        "searchBtn": "1",
    }

    response = requests.post(
        "https://startup.registroimprese.it/isin/search?0-2.0-vetrinaSearch-vetrinaSearchForm-searchBtn",
        cookies=cookies,
        headers=headers,
        data=data,
    )

    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open("proba.html", "w", encoding="utf-8") as file:
            file.write(response.text)
    print(response.status_code)


def get_json():
    response = requests.get(
        "https://b.abw.by/api/v2/adverts/1/phones", cookies=cookies, headers=headers
    )

    # Проверка кода ответа
    if response.status_code == 200:
        json_data = response.json()
        # filename = os.path.join(json_path, f"0.json")
        with open("proba.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
    else:
        print(response.status_code)


def download_xml():
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    }
    save_path = "image_sitemap_00006.xml"
    url = "https://abw.by/sitemap.xml"
    # Отправка GET-запроса на указанный URL
    response = requests.get(url, headers=headers)

    # Проверка успешности запроса
    if response.status_code == 200:
        # Сохранение содержимого в файл
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Файл успешно сохранен в: {save_path}")
    else:
        print(f"Ошибка при скачивании файла: {response.status_code}")


if __name__ == "__main__":
    get_html()
    # get_json()
    # download_xml()
