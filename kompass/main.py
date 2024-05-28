import requests
import os
import time
import glob
from selectolax.parser import HTMLParser
import csv

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
html_path = os.path.join(temp_path, "html")
page_path = os.path.join(temp_path, "page")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(html_path, exist_ok=True)
os.makedirs(page_path, exist_ok=True)


# Получаем страницы с пагинацией
def get_html_pagin():
    cookies = {
        "route": "1716888835.268.4030.250378|1ca372b33d2bad9524c20eaf607b64ca",
        "ROUTEID": ".",
        "route": "1716888835.349.4030.237230|1ca372b33d2bad9524c20eaf607b64ca",
        "JSESSIONID": "DE7E41B1DC3B0A81042561C654C234B6",
        "timezoneoffset": "-180",
        "timezonename": "Europe/Kiev",
        "_k_cty_lang": "en_UA",
        "kp_uuid": "ad065e7a-f93b-4a49-adcc-91cfead7b891",
        "axeptio_authorized_vendors": "%2Cgoogle_ads%2Cgoogle_analytics%2Cgetquanty%2CGoogle_Ads%2CGetQuanty%2C",
        "axeptio_all_vendors": "%2Cgoogle_ads%2Cgoogle_analytics%2Cgetquanty%2CGoogle_Ads%2CGetQuanty%2C",
        "axeptio_cookies": "{%22$$token%22:%22zq6e5xgx1upplr1uswx1u%22%2C%22$$date%22:%222024-05-28T09:34:21.077Z%22%2C%22$$cookiesVersion%22:{%22name%22:%22en-default_OK%22%2C%22identifier%22:%2266548c60786af5884d63e274%22}%2C%22google_ads%22:true%2C%22google_analytics%22:true%2C%22getquanty%22:true%2C%22$$googleConsentMode%22:{%22version%22:2%2C%22analytics_storage%22:%22granted%22%2C%22ad_storage%22:%22granted%22%2C%22ad_user_data%22:%22granted%22%2C%22ad_personalization%22:%22granted%22}%2C%22Google_Ads%22:true%2C%22GetQuanty%22:true%2C%22$$completed%22:true}",
        "datadome": "dNx47v9mDzCSKlW3veBRNCxeZX~YCtpsgGreDhtR2oegqek1lrsPrTjAFdZpylhqr~PWfUoRPhc9curOjcBiCl9XwCTwdErhgIw586NOZV81ylIZ59bpbmz0l0erLvao",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "dnt": "1",
        "priority": "u=0, i",
        "referer": "https://ua.kompass.com/en/searchCompanies/facet?value=RO&label=Romania&filterType=country&searchType=COMPANYNAME&checked=true",
        "sec-ch-device-memory": "8",
        "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-full-version-list": '"Google Chrome";v="125.0.6422.113", "Chromium";v="125.0.6422.113", "Not.A/Brand";v="24.0.0.0"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }

    for page in range(1, 5):

        params = {
            "tab": "cmp",
            "pageNbre": page,
            "token": "03AFcWeA7x3JPqyzvdxhaRkpKgRdHuSwZ16nuB4uISbGygB_r64FpC0RYSlzow8en6t9t8vc8kXShA_2AaLI08K6h6JoNS3iTPNoUOWPZa9gyTgJbjoOjAMCoEYwNfVN0Gwky-tQkreDoo-dx8g2D9zofjbUaFe96KmdBvcE5MEVK2S0hF7aV7xCRtcTPReyHU7ZB0_fk2qOaiw-B01tHi-7YvIuXraHH6cUlXyWjx-Ue5x4-1tmz5MyoNdGk0EcgyeRTQUMFeJwbnB-CdWcvkQAAquqdf6UKcZlV-GPWhnzmYZ5xAIapcyZUqBAbInz127S8TH_xx7ZgFWqIpwYFm-MNBdeAmGtNOSqmxeDPq6HIq3c6RnqgijtscWOsbWLVCG1_S7Spyrw-r9oDzcKL5vJbLubAkJKk3DR_NABUcoz_rzwF1c85YwlThh1UfkBZbZH6x8umyHHTZzr-CNUJ9lHT2JPyAShqAE-FrXWFqbK6leXkc503r8Xi6DHuBXK1_uYq1LLbKp_G13EsGLwH7LbvYOJphfbg0mRwJ_ivlI6NHQ22iuHVKIGYSkUC75jH-1iCEYJHq4cnrHXVYQk-JfreGU7XvTGDn3NjtRceJTn3GV2t6NxQk-o8Kucwu82fBOLoooumPLt5j1GpNsDpomERrhLZSNx8fcw",
        }
        file_name_html = os.path.join(page_path, f"0{page}.html")
        response = requests.get(
            "https://ua.kompass.com/searchCompanies/scroll",
            params=params,
            cookies=cookies,
            headers=headers,
        )
        src = response.text
        with open(file_name_html, "w", encoding="utf-8") as file:
            file.write(src)
        time.sleep(10)


# Скачиваем страницы компаний полностью
def get_html_company():
    cookies = {
        "timezoneoffset": "-180",
        "timezonename": "Europe/Kiev",
        "eqy_sessionid": "104826bb8fbfd1cf082d2f3b32ca3d66",
        "axeptio_authorized_vendors": "%2CSnapEngage%2Cfacebook_pixel%2Cgoogle_ads%2CGetQuanty%2Cgoogle_analytics%2Cshinystat%2CGoogle_Ads%2Cgetquanty%2C",
        "axeptio_all_vendors": "%2CSnapEngage%2Cfacebook_pixel%2Cgoogle_ads%2CGetQuanty%2Cgoogle_analytics%2Cshinystat%2CGoogle_Ads%2Cgetquanty%2C",
        "axeptio_cookies": "{%22$$token%22:%22ff7bfox8oh8mep3ylar4xr%22%2C%22$$date%22:%222024-03-29T11:26:53.533Z%22%2C%22$$cookiesVersion%22:{%22name%22:%22fr-FR%22%2C%22identifier%22:%226053a2752c0a5b3e720259b6%22}%2C%22SnapEngage%22:true%2C%22facebook_pixel%22:true%2C%22google_ads%22:true%2C%22GetQuanty%22:true%2C%22google_analytics%22:true%2C%22shinystat%22:true%2C%22$$googleConsentMode%22:{%22version%22:2%2C%22analytics_storage%22:%22granted%22%2C%22ad_storage%22:%22granted%22%2C%22ad_user_data%22:%22granted%22%2C%22ad_personalization%22:%22granted%22}%2C%22Google_Ads%22:true%2C%22getquanty%22:true%2C%22$$completed%22:true}",
        "_k_cty_lang": "en_RS",
        "ROUTEID": ".",
        "_ga": "GA1.1.1244701985.1716645891",
        "timezoneoffset": "-180",
        "timezonename": "Europe/Kiev",
        "_gcl_au": "1.1.1289665636.1716645891",
        "_ga": "GA1.3.1244701985.1716645891",
        "eqy_sessionid": "",
        "_referrer_og": "https%3A%2F%2Ffreelancehunt.com%2F",
        "route": "1716872871.613.6745.794749|1ca372b33d2bad9524c20eaf607b64ca",
        "JSESSIONID": "E43185CA1AB596F067FA52405AA07167",
        "_gid": "GA1.3.2065520309.1716872871",
        "__gads": "ID=115c18f97f7d58c3:T=1716872871:RT=1716872871:S=ALNI_MYm4FL-UNNAo_MNDyWWu38d2EK71w",
        "__gpi": "UID=00000e30c3794823:T=1716872871:RT=1716872871:S=ALNI_MZhhegKJEbDxKd1_RSGOpL-1FJ9EA",
        "__eoi": "ID=effd6452dea0561d:T=1716872871:RT=1716872871:S=AA-AfjYKCFLjEhLpxMaYeefxJG2K",
        "cluid": "13F3FEC4-5532-39AF-8318-47FD2D5EF62C",
        "_first_pageview": "1",
        "_jsuid": "1841142022",
        "_ga_3XPJBXM25M": "GS1.3.1716872871.2.1.1716872932.0.0.0",
        "_ga_F7YPZ3JHHR": "GS1.3.1716872871.2.1.1716872932.60.0.0",
        "_ga_H9RY6SXL1H": "GS1.1.1716872871.2.1.1716872932.0.0.0",
        "_ga_YFM4S8XBVP": "GS1.1.1716872871.2.1.1716872932.0.0.0",
        "_ga_J30PXCM6CP": "GS1.1.1716872871.2.1.1716872932.0.0.0",
        "FCNEC": "%5B%5B%22AKsRol8MtMxXNpSc3W9ynKNRnznIYo4oskrFl-OoZnUukKlzj79eqQauojiXu7pDlIiSjyKOx-LY6ntraVo0bGXyCRK8DVkxv1WStdIFKma-Ui_AMUB1Ud50LHzjBCoQfBTx0lS0U4YaQVP4kC-Wxp9cQTy5QfxSFA%3D%3D%22%5D%5D",
        "datadome": "XFsWIhqw88ZPaBqzxpyN3FrrBihxqpetb_L41XFiImW6CXlRLuE_n_kGxcjH1Nz9fZJ0ihTyMc_B~fsF1JYGAxJwXS2Z43dCTJhfz6cWtf3v4DLThAtaN8zFQytxiXSl",
        "kp_uuid": "5c040bb2-c4c3-4bed-8759-df240f2ee4d1",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "cache-control": "max-age=0",
        "dnt": "1",
        "priority": "u=0, i",
        "sec-ch-device-memory": "8",
        "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-full-version-list": '"Google Chrome";v="125.0.6422.113", "Chromium";v="125.0.6422.113", "Not.A/Brand";v="24.0.0.0"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }
    file_path = "links.txt"
    with open(file_path, "r") as file:
        lines = file.readlines()
    for line in lines:
        category, url = line.strip().split("|")
        url_name = url.split("/")[-2]
        file_name_html = os.path.join(html_path, f"{url_name}.html")
        if not os.path.exists(file_name_html):
            response = requests.get(url, cookies=cookies, headers=headers)
            # response.encoding = 'utf-8'  # Set encoding to UTF-8
            src = response.text
            with open(file_name_html, "w", encoding="utf-8") as file:
                file.write(src)
            time.sleep(10)


# Парсим страницы компаний
def parsing_html():
    all_datas = []
    file_path = "links.txt"
    with open(file_path, "r") as file:
        lines = file.readlines()
    for line in lines:
        category, url = line.strip().split("|")
        data = {"category": category, "url": url}
        all_datas.append(data)
    folder = os.path.join(html_path, "*.html")
    files_html = glob.glob(folder)
    company_datas = []
    for item in files_html:
        with open(item, encoding="utf-8") as file:
            src = file.read()
        find_company = os.path.splitext(os.path.basename(item))[0]
        parser = HTMLParser(src)
        company_name = parser.css_first(
            "#productDetailUpdateable > div.container.containerCompany > div.headerCompany > div > div.headCol1.headColumn > div > div.headCol1.blockNameHead > h1"
        ).text(strip=True)
        company_country = parser.css_first(
            "#productDetailUpdateable > div.container.containerCompany > div.headerCompany > div > div.headCol1.headColumn > div > div.headCol1.blockNameHead > div > p > span.spRight"
        ).text(strip=True)
        company_www_node = parser.css_first("#webSite_presentation_0")
        company_www = company_www_node.text(strip=True) if company_www_node else None

        company_phone_node = parser.css_first(
            'input[id*="freePhone-contactCompanyForCompany"]'
        )
        company_phone = (
            company_phone_node.attributes.get("value") if company_phone_node else None
        )
        company_category = None
        company_url = None
        for data in all_datas:
            if find_company in data["url"]:
                company_category = data["category"]
                company_url = data["url"]
        company_data = {
            "company_name": company_name,
            "company_country": company_country,
            "company_www": company_www,
            "company_phone": company_phone,
            "company_category": company_category,
            "company_url": company_url,
        }
        company_datas.append(company_data)
    csv_file_name = "companies.csv"
    with open(csv_file_name, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=company_datas[0].keys(), delimiter=";")
        writer.writeheader()
        for company_data in company_datas:
            writer.writerow(company_data)


# Получаем ссылки на компании
def parsing_pagin():
    folder = os.path.join(page_path, "*.html")
    files_html = glob.glob(folder)
    company_url = []
    for item in files_html:
        with open(item, encoding="utf-8") as file:
            src = file.read()
        parser = HTMLParser(src)
        # Ищем все элементы a внутри заданной структуры div
        links = parser.css("div > div.row.rowTop.margB0 > div > a")

        # Извлекаем атрибуты href из каждого найденного элемента
        hrefs = [
            company_url.append(f"https://ua.kompass.com/{link.attributes.get('href')}")
            for link in links
        ]
    print(company_url)


def get_html_company_new():
    cookies = {
        "timezoneoffset": "-180",
        "timezonename": "Europe/Kiev",
        "timezoneoffset": "-180",
        "timezonename": "Europe/Kiev",
        "_ga": "GA1.1.1244701985.1716645891",
        "_gcl_au": "1.1.1289665636.1716645891",
        "route": "1716881604.615.6748.869820|1ca372b33d2bad9524c20eaf607b64ca",
        "JSESSIONID": "B2C301CE275D4888E3B7CFD840F7302E",
        "ROUTEID": ".",
        "__gads": "ID=115c18f97f7d58c3:T=1716872871:RT=1716883601:S=ALNI_MYm4FL-UNNAo_MNDyWWu38d2EK71w",
        "__gpi": "UID=00000e30c3794823:T=1716872871:RT=1716883601:S=ALNI_MZhhegKJEbDxKd1_RSGOpL-1FJ9EA",
        "__eoi": "ID=effd6452dea0561d:T=1716872871:RT=1716883601:S=AA-AfjYKCFLjEhLpxMaYeefxJG2K",
        "FCNEC": "%5B%5B%22AKsRol9muSNfg2TAh0FvuWRW11OjdZRL-mAC0QEtgQtT8moXqfKIC2xDFD7YuIja6OuQadO4XOOsHbiuzrGkVtrZXEG9VlKPxG30jglz1OFS2i-GPP9tCRwEjhrL0Uy6OolRYijqxIUFlEOpDBs-9klTlAjyoO9vBg%3D%3D%22%5D%5D",
        "_k_cty_lang": "en_UA",
        "_ga_H9RY6SXL1H": "GS1.1.1716882113.3.1.1716884553.0.0.0",
        "_ga_YFM4S8XBVP": "GS1.1.1716882113.3.1.1716884553.0.0.0",
        "_ga_J30PXCM6CP": "GS1.1.1716882113.3.1.1716884553.0.0.0",
        "axeptio_authorized_vendors": "%2Cgoogle_ads%2Cgoogle_analytics%2Cgetquanty%2CGoogle_Ads%2CGetQuanty%2C",
        "axeptio_all_vendors": "%2Cgoogle_ads%2Cgoogle_analytics%2Cgetquanty%2CGoogle_Ads%2CGetQuanty%2C",
        "axeptio_cookies": "{%22$$token%22:%22n2821ysns7r5bwccph0n%22%2C%22$$date%22:%222024-05-28T08:23:15.831Z%22%2C%22$$cookiesVersion%22:{%22name%22:%22en-default_OK%22%2C%22identifier%22:%2266548c60786af5884d63e274%22}%2C%22google_ads%22:true%2C%22google_analytics%22:true%2C%22getquanty%22:true%2C%22$$googleConsentMode%22:{%22version%22:2%2C%22analytics_storage%22:%22granted%22%2C%22ad_storage%22:%22granted%22%2C%22ad_user_data%22:%22granted%22%2C%22ad_personalization%22:%22granted%22}%2C%22Google_Ads%22:true%2C%22GetQuanty%22:true%2C%22$$completed%22:true}",
        "datadome": "spDeko5SWKPIltOItA~Ix4AOr8oxUUJO0P7w72V~wA66UsUI9is5tsD7NIpMS_g~capuDIrNaQFXiJ81XUnwiQDRw84sA0jzYK2HzJ8fwz9TcoPOr6Co1kZnBtqem~VF",
        "kp_uuid": "dc9a82ba-be8f-4e97-aa1f-c17aad89f754",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://ua.kompass.com/searchCompanies/scroll?tab=cmp&pageNbre=6&token=03AFcWeA57DjgDHhLrlEYJBzo3pMwkp0lHUJaoiRBWU8mSl3vIXws7faQ5ztYk__dz_CYxdLlOvz2T6o6Se7Ma_RhEi8N3TmOf7LMmYKs7JMoeN3juqD-CKvcnM23Mvof6Gq9ALRroUAvLVEvLWMEbh21OzYLhjtoBYdskhd3huGr22XnLyvGpuCIr46zGAMkUzkH5aV4msqGpxtr6Tb3SuMOjCsFM_OUj8nKNgpga8oof58oN2GV4bdp6rlpb1kQ_gK4T7f9vjAWcgeIZ53AGGEDn4YpjNj8Iux3WkJfbfiU67AvcXtA0GrytkS4U4ILbIxBieC7yuSTujlUvabFqqma8KXJgELTtGeZ-8Q05G0D9AiC28m2hic1_uz5PXfrmG6Tk11VuczgsvhdSUpjUQ7Uh4O8dWo_Q_6uttn3uABGFpbJHnekoIWoCYVQa3E10PNm3wy9OX6aBEtCO6Iwc5-hGledGiLz4KQq0J6PGeE7rbwezTdl2hhO0JYjW3Htrikq3S1YAJE38p8BLg873TFt2gbtWpUzL8x-zJthXH_-9niIopggxTl07aRB7Cngq4Kuaxqy5O6qZjm32DARQaYMMQABVoxZiD9YZnKiEFZFlg1bCvEM65Y-NiexmpmwJjNmTzoKJhAeeGv7b_UEQdC24y3ybcUVfVuUW5HD5_GYLGjmxISq7szA",
        "sec-ch-device-memory": "8",
        "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-full-version-list": '"Google Chrome";v="125.0.6422.113", "Chromium";v="125.0.6422.113", "Not.A/Brand";v="24.0.0.0"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }
    file_path = "links.txt"
    with open(file_path, "r") as file:
        lines = file.readlines()
    for line in lines:
        url = line.strip()
        url_name = url.split("/")[-2]
        file_name_html = os.path.join(html_path, f"{url_name}.html")
        if not os.path.exists(file_name_html):
            response = requests.get(url, cookies=cookies, headers=headers)
            # response.encoding = 'utf-8'  # Set encoding to UTF-8
            src = response.text
            with open(file_name_html, "w", encoding="utf-8") as file:
                file.write(src)
            time.sleep(10)


def parsing_html_new():
    all_datas = []

    folder = os.path.join(html_path, "*.html")
    files_html = glob.glob(folder)
    company_datas = []
    for item in files_html:
        with open(item, encoding="utf-8") as file:
            src = file.read()
        find_company = os.path.splitext(os.path.basename(item))[0]
        parser = HTMLParser(src)
        company_name = parser.css_first(
            "#productDetailUpdateable > div.container.containerCompany > div.headerCompany > div > div.headCol1.headColumn > div > div.headCol1.blockNameHead > h1"
        ).text(strip=True)
        company_country = parser.css_first(
            "#productDetailUpdateable > div.container.containerCompany > div.headerCompany > div > div.headCol1.headColumn > div > div.headCol1.blockNameHead > div > p > span.spRight"
        ).text(strip=True)
        company_www_node = parser.css_first("#webSite_presentation_0")
        company_www = company_www_node.text(strip=True) if company_www_node else None

        company_phone_node = parser.css_first(
            'input[id*="freePhone-contactCompanyForCompany"]'
        )
        company_phone = (
            company_phone_node.attributes.get("value") if company_phone_node else None
        )
        company_category = None
        company_url = None
        company_data = {
            "company_name": company_name,
            "company_www": company_www,
            "company_phone": company_phone,
        }
        company_datas.append(company_data)
    csv_file_name = "companies.csv"
    with open(csv_file_name, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=company_datas[0].keys(), delimiter=";")
        writer.writeheader()
        for company_data in company_datas:
            writer.writerow(company_data)


if __name__ == "__main__":
    # get_html_pagin()
    # parsing_pagin()
    # get_html_company()
    # get_html_company_new()
    # parsing_html()
    parsing_html_new()
