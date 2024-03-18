from bs4 import BeautifulSoup
import csv
import glob
import requests
import json
import os
import random
import time
import csv
from proxi import proxies
from selenium.webdriver.chrome.service import Service
from selenium import webdriver


def get_request():
    cookies = {
        'visid_incap_242093': '/HD7mKKsQ6G7gDsklJSPfCiNpWQAAAAAQUIPAAAAAABX+/wq/GldPxN2hTzvXtI9',
        'incap_ses_323_242093': '0J1xL08wnkbqmUi0wId7BCiNpWQAAAAAu/wMleTtB0gvWw/edb+KYA==',
        'g2usersessionid': '023c5fb0412f4eeeabb81f3a16fe981a',
        'G2JSESSIONID': 'FFBA58978B544C41C9C38BDBE6012C63-n1',
        'userLang': 'en',
        'nlbi_242093': 'o0IsM2tuB2yjCyk3JDHybgAAAABJ8NpI3kDkI8cI8wNiVg8r',
        'userCategory': 'PU',
        'timezone': 'Europe%2FKiev',
        'nlbi_242093_2147483392': 'tpuOQ5JGAVx/DtteJDHybgAAAADqSMxl3e/th5uvsUtQ9ys5',
        'reese84': '3:MIVtSpmsCY0FOHA09urRKQ==:vLEf9qESbUteJTxUXDkiHHC6/+PEInKZROzPxCyayrdMRaV/DXQhYLXLosis2uh+SHNh/o3I4dOE1RbpKPj+9nYLL6r9V4WwakHljTcMZ6N19uD/unrgQtgjaZCnZbfIvKP0FgUncJJLlXvhnoXDWjSDCjfel+5lB9yJSldsOyuYnSVnfU5PK4OAqxGGQ1VabnqEy5ygvGvtGmjvNC9tt5fQOKdQJIX1tvyN1KZX9VpxCrR9KDbIDn7mK/FZSJ4X/rzx0MWJfafgsmF3ieJsC/ajfR/wCWMgsYHDoiVr57u0t7iC4jFt5AA0R4ccT3bC4QFdAK5HXsz1T9DicNKJ22l6IGCB7nVdgwhf57SnCmLralEj9Kq5JBd1VGCnZiJ6av6dwxYr5nXtQm0RxuCYZy3KZSOlxORW8k4IMCtB5COJINnsks+RpDdz3uOVDEk81up/7swEoY17ZRkLeVQPqGuF7bfjEow8By7qFKMy79X+IZk3/0rBHCBK1TEV2DfSipHcQ3q0FKCzNKhc3Dc9cw==:+k9Ge5nP5yKkFjtVkPFi8ZxqcOnCMhg+TvJpjGumuUs=',
        '_gcl_au': '1.1.98825793.1688571180',
        '_ga': 'GA1.2.1755939870.1688571180',
        '_gid': 'GA1.2.1493294689.1688571180',
        '_gat_UA-90930613-6': '1',
        '_uetsid': '392f34101b4911eeb4b20d2d8e1dcb8b',
        '_uetvid': '392f45301b4911eebfa43969372e5ed1',
        '_fbp': 'fb.1.1688571180107.576491671',
        '_tt_enable_cookie': '1',
        '_ttp': 'a4nDIBvtjS-sSBg9tKFnZhW_FT1',
        '_clck': '1qdze69|2|fd1|0|1281',
        'cto_bundle': 'G8UHWl94Y21FUEJVaFN3N3NySjJqcEh2MHQzUnNQSlduYWRCSnBwcG1hbUxJZjliNXVlVkJvSGozUVFLUXAweVE1bTdXMTRzNHk3WWRlbHlQeGN3Tm9tMVUwUVIxV0NkOXBaRFdQU2klMkZzbWk4cWpSaDhlMWhBdzZVbTBkQ0dSc0t3JTJCWFE',
        '_cc_id': 'b836aeb22a0a3a359c23e8afd743771c',
        'panoramaId_expiry': '1689175980866',
        'panoramaId': 'b9d76f8aff9339cf023dc09cba4d16d539384251f146d8ab5b6b99fd099daf26',
        'panoramaIdType': 'panoIndiv',
        '_clsk': 's6h0np|1688571180947|1|0|o.clarity.ms/collect',
        'copartTimezonePref': '%7B%22displayStr%22%3A%22GMT%2B3%22%2C%22offset%22%3A3%2C%22dst%22%3Atrue%2C%22windowsTz%22%3A%22Europe%2FKiev%22%7D',
        'FCNEC': '%5B%5B%22AKsRol99YIkBlUlshr-rZkLVTCoroq-b6ijXggvuNswvHx-SbvSR9CPsCBU1zA9q-oyNa0y269TadQ0q1egY7UIIO3h5y-IavxXo-Hkf541VSSQG9IemMM4iwYnytonOgmoO3gjt0sL3Xovjl0Z4Htm9bKgFmQZlSA%3D%3D%22%5D%2Cnull%2C%5B%5D%5D',
        '_ga_VMJJLGQLHF': 'GS1.1.1688571179.1.1.1688571187.52.0.0',
        's_ppv': '100',
        '__gads': 'ID=4d25351eaa983cce:T=1688571188:RT=1688571188:S=ALNI_Mb-WoUPX53hCPeXgeNNb_2rdapMNQ',
        '__gpi': 'UID=00000c373144cb15:T=1688571188:RT=1688571188:S=ALNI_MatCcOP289TJWma2keSKBwx5oMsVQ',
        's_fid': '604563B7FACDB9E9-22394B2B905608F2',
        's_depth': '1',
        's_pv': 'no%20value',
        's_vnum': '1691163188651%26vn%3D1',
        's_invisit': 'true',
        's_lv_s': 'First%20Visit',
        'search-table-rows': '20',
        's_nr': '1688571192347-New',
        's_lv': '1688571192347',
    }

    headers = {
        'authority': 'www.copart.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ru',
        'access-control-allow-headers': 'Content-Type, X-XSRF-TOKEN',
        'content-type': 'application/json',
        # 'cookie': 'visid_incap_242093=/HD7mKKsQ6G7gDsklJSPfCiNpWQAAAAAQUIPAAAAAABX+/wq/GldPxN2hTzvXtI9; incap_ses_323_242093=0J1xL08wnkbqmUi0wId7BCiNpWQAAAAAu/wMleTtB0gvWw/edb+KYA==; g2usersessionid=023c5fb0412f4eeeabb81f3a16fe981a; G2JSESSIONID=FFBA58978B544C41C9C38BDBE6012C63-n1; userLang=en; nlbi_242093=o0IsM2tuB2yjCyk3JDHybgAAAABJ8NpI3kDkI8cI8wNiVg8r; userCategory=PU; timezone=Europe%2FKiev; nlbi_242093_2147483392=tpuOQ5JGAVx/DtteJDHybgAAAADqSMxl3e/th5uvsUtQ9ys5; reese84=3:MIVtSpmsCY0FOHA09urRKQ==:vLEf9qESbUteJTxUXDkiHHC6/+PEInKZROzPxCyayrdMRaV/DXQhYLXLosis2uh+SHNh/o3I4dOE1RbpKPj+9nYLL6r9V4WwakHljTcMZ6N19uD/unrgQtgjaZCnZbfIvKP0FgUncJJLlXvhnoXDWjSDCjfel+5lB9yJSldsOyuYnSVnfU5PK4OAqxGGQ1VabnqEy5ygvGvtGmjvNC9tt5fQOKdQJIX1tvyN1KZX9VpxCrR9KDbIDn7mK/FZSJ4X/rzx0MWJfafgsmF3ieJsC/ajfR/wCWMgsYHDoiVr57u0t7iC4jFt5AA0R4ccT3bC4QFdAK5HXsz1T9DicNKJ22l6IGCB7nVdgwhf57SnCmLralEj9Kq5JBd1VGCnZiJ6av6dwxYr5nXtQm0RxuCYZy3KZSOlxORW8k4IMCtB5COJINnsks+RpDdz3uOVDEk81up/7swEoY17ZRkLeVQPqGuF7bfjEow8By7qFKMy79X+IZk3/0rBHCBK1TEV2DfSipHcQ3q0FKCzNKhc3Dc9cw==:+k9Ge5nP5yKkFjtVkPFi8ZxqcOnCMhg+TvJpjGumuUs=; _gcl_au=1.1.98825793.1688571180; _ga=GA1.2.1755939870.1688571180; _gid=GA1.2.1493294689.1688571180; _gat_UA-90930613-6=1; _uetsid=392f34101b4911eeb4b20d2d8e1dcb8b; _uetvid=392f45301b4911eebfa43969372e5ed1; _fbp=fb.1.1688571180107.576491671; _tt_enable_cookie=1; _ttp=a4nDIBvtjS-sSBg9tKFnZhW_FT1; _clck=1qdze69|2|fd1|0|1281; cto_bundle=G8UHWl94Y21FUEJVaFN3N3NySjJqcEh2MHQzUnNQSlduYWRCSnBwcG1hbUxJZjliNXVlVkJvSGozUVFLUXAweVE1bTdXMTRzNHk3WWRlbHlQeGN3Tm9tMVUwUVIxV0NkOXBaRFdQU2klMkZzbWk4cWpSaDhlMWhBdzZVbTBkQ0dSc0t3JTJCWFE; _cc_id=b836aeb22a0a3a359c23e8afd743771c; panoramaId_expiry=1689175980866; panoramaId=b9d76f8aff9339cf023dc09cba4d16d539384251f146d8ab5b6b99fd099daf26; panoramaIdType=panoIndiv; _clsk=s6h0np|1688571180947|1|0|o.clarity.ms/collect; copartTimezonePref=%7B%22displayStr%22%3A%22GMT%2B3%22%2C%22offset%22%3A3%2C%22dst%22%3Atrue%2C%22windowsTz%22%3A%22Europe%2FKiev%22%7D; FCNEC=%5B%5B%22AKsRol99YIkBlUlshr-rZkLVTCoroq-b6ijXggvuNswvHx-SbvSR9CPsCBU1zA9q-oyNa0y269TadQ0q1egY7UIIO3h5y-IavxXo-Hkf541VSSQG9IemMM4iwYnytonOgmoO3gjt0sL3Xovjl0Z4Htm9bKgFmQZlSA%3D%3D%22%5D%2Cnull%2C%5B%5D%5D; _ga_VMJJLGQLHF=GS1.1.1688571179.1.1.1688571187.52.0.0; s_ppv=100; __gads=ID=4d25351eaa983cce:T=1688571188:RT=1688571188:S=ALNI_Mb-WoUPX53hCPeXgeNNb_2rdapMNQ; __gpi=UID=00000c373144cb15:T=1688571188:RT=1688571188:S=ALNI_MatCcOP289TJWma2keSKBwx5oMsVQ; s_fid=604563B7FACDB9E9-22394B2B905608F2; s_depth=1; s_pv=no%20value; s_vnum=1691163188651%26vn%3D1; s_invisit=true; s_lv_s=First%20Visit; search-table-rows=20; s_nr=1688571192347-New; s_lv=1688571192347',
        'dnt': '1',
        'origin': 'https://www.copart.com',
        'referer': 'https://www.copart.com/lotSearchResults?free=true&query=&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22FETI%22:%5B%22buy_it_now_code:B1%22%5D%7D,%22searchName%22:%22%22,%22watchListOnly%22:false,%22freeFormSearch%22:false%7D',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
        'x-xsrf-token': '1ebf6baf-d0db-4be9-95b4-7aa52967e6cf',
    }

    ad = 19209
    page_ad = ad // 100
    start = 0
    page = 0
    for i in range(page_ad + 1):
        filename = f"c:\\DATA\\copart\\list\\data_{page}.json"
        if not os.path.exists(filename):
            # Создаем сессию

            # for i in range(page_ad + 1):
            pause_time = random.randint(5, 10)
            proxy = random.choice(proxies)
            proxy_host = proxy[0]
            proxy_port = proxy[1]
            proxy_user = proxy[2]
            proxy_pass = proxy[3]

            proxi = {
                'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
                'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
            }

            json_data = {
                'query': [
                    '*',
                ],
                'filter': {
                    'FETI': [
                        'buy_it_now_code:B1',
                    ],
                },
                'sort': [
                    'member_damage_group_priority asc',
                    'auction_date_type desc',
                    'auction_date_utc asc',
                ],
                'page': page,
                'size': 100,
                'start': start,
                'watchListOnly': False,
                'freeFormSearch': False,
                'hideImages': False,
                'defaultSort': False,
                'specificRowProvided': False,
                'displayName': '',
                'searchName': '',
                'backUrl': '',
                'includeTagByField': {},
                'rawParams': {},
            }

            try:
                response = requests.post('https://www.copart.com/public/lots/search-results', cookies=cookies,
                                         headers=headers, json=json_data)
            except:
                print(response.status_code)
                continue
            data = response.json()

            with open(filename, 'w') as f:
                json.dump(data, f)
            time.sleep(pause_time)
        page += 1
        start += 20


def get_id_ad_and_url():
    folders_html = r"c:\DATA\copart\list\*.json"
    files_html = glob.glob(folders_html)
    with open(f"url.csv", 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for i in files_html:
            with open(i, 'r') as f:
                json_data = json.load(f)
            content = json_data['data']['results']['content']
            for c in content:
                url_ad = f'https://www.copart.com/public/data/lotdetails/solr/{c["ln"]}'
                writer.writerow([url_ad])


def get_product():
    cookies = {
        'g2usersessionid': '7d90a88ea25ffafd5ad77a7459772725',
        'G2JSESSIONID': '7483EE8EC05638107CB98018D0467082-n1',
        'visid_incap_242093': 'LYAkz4NlSnaZAdQ7/Lz9NHCCpmQAAAAAQUIPAAAAAACr1BoBXxC2bzgxKHks7fT8',
        'nlbi_242093': 'U28uLqdBrTyNcpeBJDHybgAAAAD7OXqz5spNSnSSyxnVExbp',
        'incap_ses_323_242093': 'XZswYRV6WxKBfOW0wId7BOaJpmQAAAAA+JefXX33FwdIKQRRHnXXuw==',
        'userLang': 'en',
        'timezone': 'Europe%2FKiev',
        'userCategory': 'RPU',
        '_gcl_au': '1.1.734039856.1688635882',
        '_fbp': 'fb.1.1688635882557.1537327702',
        '_tt_enable_cookie': '1',
        '_ttp': 'raP6QJGH-q9v1RT-1yeNGzd7Mxt',
        '_clck': '1s3ezr6|2|fd2|0|1282',
        'cto_bundle': 'Ioo4xF9BZEtiT052RWtxZWU0SXVNTkhqcmdhMUJ4SnRlaWNmYm42emV1RXJYNWVZWFZnNXhjQTgwMWxGRGh2ZlhiTndydGZYY1hIU2pXV0lXTTluQW0zOHVrR0IlMkZ0dUptQTRGWFhFJTJCQ1lXN0dBbkZjNXFpSFQwUlVlajhBcjNseEZnTFo',
        '_cc_id': '44aac68926c7c1ec94653f18eb329f97',
        'panoramaId_expiry': '1689240683662',
        'panoramaId': 'b9d76f8aff9339cf023dc09cba4d16d539384251f146d8ab5b6b99fd099daf26',
        'panoramaIdType': 'panoIndiv',
        '_gid': 'GA1.2.613538279.1688635884',
        'copartTimezonePref': '%7B%22displayStr%22%3A%22GMT%2B3%22%2C%22offset%22%3A3%2C%22dst%22%3Atrue%2C%22windowsTz%22%3A%22Europe%2FKiev%22%7D',
        '__gads': 'ID=75a829e53874e4c7:T=1688636435:RT=1688636435:S=ALNI_Mb2WDKDXoKdex0KBWN4Z8MlSb9IRg',
        '__gpi': 'UID=00000c37477a230b:T=1688636435:RT=1688636435:S=ALNI_MY41As8du5hrbvl4oCDICFEvEVdzw',
        'usersessionid': 'a464acc53ef4b4804afa8864eaa2ad5e',
        'OAID': '849fd5ee6e33135619591da258446493',
        '_uetsid': 'dee6e7101bdf11ee9fcd99c790a27111',
        '_uetvid': 'dee6f5501bdf11eeb4e34dc136db99c3',
        '_ga': 'GA1.2.627396451.1688635883',
        'FCNEC': '%5B%5B%22AKsRol-ahIv_NqEERa_fKy_y2bcVAamP6zEGlmwbtx9z54mdPv7rTOwJpgA68ddJKZuvOPm3CX8SvjNxAR1m5UQwTjCYUBH0R7h5FoWwWkPk2xI8s2KaBsum1_G9omuyBsbjwXuEFqccHQ37TAcoArHj-Q1mRBEDig%3D%3D%22%5D%2Cnull%2C%5B%5D%5D',
        'reese84': '3:5OpkjOohiRMB8e1P6Unp6w==:YQ23cI0xGDfJMssT0YCLA73mXgd3efjEs1qhCKUDOwHo0EuAJnGfmpv2X7gKFoxrIL9tXRyQkbThsJJPT73MDSLSZr+oVS7KIv9Ef2Yw2PldMKkjjQF5nZ+2Iz1UG4b0RHt4ZOpp6sIERw84CT1rbWrc0lQRSauUUQ2LZ6Hd2BLKfYdMbBcD+PTRMsQAmO5PfpS6MlPlvajX6k9lvT+EnKyfYuap3ps/P3fa1aDh0+5wo9EBh0bnkay3Gbpm6JybsHqM7Nuloc6BTSVxajJ/iGLbQA/mkPiVYTOoJiQbyccgTRhInB64OIKLFElkleYua2+VvvEti7Ldagz9TFJBbUHNv4e4i5nMciuBRTD/Z+RvlAx4KHW1+8ce6pGzHTki3k93ayaVfgdZ2TzKhTIdcjjOEhDVpyQMh7CTkIgtdFrMEOnL7U22Jsvsd81EG8VnSUK1QX3fYMgB1Vb0nccgVA2ZW4365zL+ChX5sm103LdjOlO8d+gFoCrP+iA7WJdyyn3EPT2nYju9B+KlnHS7uA==:fELHh20W6mwx8odd/IH9HS77kpkUg9LC+6cPXQoP0FU=',
        's_fid': '619667AAD0D63546-09C78E4133941BD1',
        's_depth': '1',
        's_pv': 'no%20value',
        's_nr': '1688639132153-New',
        's_vnum': '1691231132153%26vn%3D1',
        's_invisit': 'true',
        's_lv': '1688639132153',
        's_lv_s': 'First%20Visit',
        '_clsk': 'bywam4|1688639132669|9|0|o.clarity.ms/collect',
        '_ga_VMJJLGQLHF': 'GS1.1.1688639133.2.0.1688639133.60.0.0',
        '_gat_UA-90930613-6': '1',
        'nlbi_242093_2147483392': 'NyYKDiJWbWo8i2l2JDHybgAAAABp+++HjjBDF1sWbTpvNhbG',
    }

    headers = {
        'authority': 'www.copart.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru',
        'cache-control': 'no-cache',
        # 'cookie': 'g2usersessionid=7d90a88ea25ffafd5ad77a7459772725; G2JSESSIONID=7483EE8EC05638107CB98018D0467082-n1; visid_incap_242093=LYAkz4NlSnaZAdQ7/Lz9NHCCpmQAAAAAQUIPAAAAAACr1BoBXxC2bzgxKHks7fT8; nlbi_242093=U28uLqdBrTyNcpeBJDHybgAAAAD7OXqz5spNSnSSyxnVExbp; incap_ses_323_242093=XZswYRV6WxKBfOW0wId7BOaJpmQAAAAA+JefXX33FwdIKQRRHnXXuw==; userLang=en; timezone=Europe%2FKiev; userCategory=RPU; _gcl_au=1.1.734039856.1688635882; _fbp=fb.1.1688635882557.1537327702; _tt_enable_cookie=1; _ttp=raP6QJGH-q9v1RT-1yeNGzd7Mxt; _clck=1s3ezr6|2|fd2|0|1282; cto_bundle=Ioo4xF9BZEtiT052RWtxZWU0SXVNTkhqcmdhMUJ4SnRlaWNmYm42emV1RXJYNWVZWFZnNXhjQTgwMWxGRGh2ZlhiTndydGZYY1hIU2pXV0lXTTluQW0zOHVrR0IlMkZ0dUptQTRGWFhFJTJCQ1lXN0dBbkZjNXFpSFQwUlVlajhBcjNseEZnTFo; _cc_id=44aac68926c7c1ec94653f18eb329f97; panoramaId_expiry=1689240683662; panoramaId=b9d76f8aff9339cf023dc09cba4d16d539384251f146d8ab5b6b99fd099daf26; panoramaIdType=panoIndiv; _gid=GA1.2.613538279.1688635884; copartTimezonePref=%7B%22displayStr%22%3A%22GMT%2B3%22%2C%22offset%22%3A3%2C%22dst%22%3Atrue%2C%22windowsTz%22%3A%22Europe%2FKiev%22%7D; __gads=ID=75a829e53874e4c7:T=1688636435:RT=1688636435:S=ALNI_Mb2WDKDXoKdex0KBWN4Z8MlSb9IRg; __gpi=UID=00000c37477a230b:T=1688636435:RT=1688636435:S=ALNI_MY41As8du5hrbvl4oCDICFEvEVdzw; usersessionid=a464acc53ef4b4804afa8864eaa2ad5e; OAID=849fd5ee6e33135619591da258446493; _uetsid=dee6e7101bdf11ee9fcd99c790a27111; _uetvid=dee6f5501bdf11eeb4e34dc136db99c3; _ga=GA1.2.627396451.1688635883; FCNEC=%5B%5B%22AKsRol-ahIv_NqEERa_fKy_y2bcVAamP6zEGlmwbtx9z54mdPv7rTOwJpgA68ddJKZuvOPm3CX8SvjNxAR1m5UQwTjCYUBH0R7h5FoWwWkPk2xI8s2KaBsum1_G9omuyBsbjwXuEFqccHQ37TAcoArHj-Q1mRBEDig%3D%3D%22%5D%2Cnull%2C%5B%5D%5D; reese84=3:5OpkjOohiRMB8e1P6Unp6w==:YQ23cI0xGDfJMssT0YCLA73mXgd3efjEs1qhCKUDOwHo0EuAJnGfmpv2X7gKFoxrIL9tXRyQkbThsJJPT73MDSLSZr+oVS7KIv9Ef2Yw2PldMKkjjQF5nZ+2Iz1UG4b0RHt4ZOpp6sIERw84CT1rbWrc0lQRSauUUQ2LZ6Hd2BLKfYdMbBcD+PTRMsQAmO5PfpS6MlPlvajX6k9lvT+EnKyfYuap3ps/P3fa1aDh0+5wo9EBh0bnkay3Gbpm6JybsHqM7Nuloc6BTSVxajJ/iGLbQA/mkPiVYTOoJiQbyccgTRhInB64OIKLFElkleYua2+VvvEti7Ldagz9TFJBbUHNv4e4i5nMciuBRTD/Z+RvlAx4KHW1+8ce6pGzHTki3k93ayaVfgdZ2TzKhTIdcjjOEhDVpyQMh7CTkIgtdFrMEOnL7U22Jsvsd81EG8VnSUK1QX3fYMgB1Vb0nccgVA2ZW4365zL+ChX5sm103LdjOlO8d+gFoCrP+iA7WJdyyn3EPT2nYju9B+KlnHS7uA==:fELHh20W6mwx8odd/IH9HS77kpkUg9LC+6cPXQoP0FU=; s_fid=619667AAD0D63546-09C78E4133941BD1; s_depth=1; s_pv=no%20value; s_nr=1688639132153-New; s_vnum=1691231132153%26vn%3D1; s_invisit=true; s_lv=1688639132153; s_lv_s=First%20Visit; _clsk=bywam4|1688639132669|9|0|o.clarity.ms/collect; _ga_VMJJLGQLHF=GS1.1.1688639133.2.0.1688639133.60.0.0; _gat_UA-90930613-6=1; nlbi_242093_2147483392=NyYKDiJWbWo8i2l2JDHybgAAAABp+++HjjBDF1sWbTpvNhbG',
        'dnt': '1',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    with open("url.csv", newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        counter = 0
        for url in urls:
            filename = f"c:\\DATA\\copart\\product\\data_{counter}.json"
            if not os.path.exists(filename):
                # def get_chromedriver():
                #     chrome_options = webdriver.ChromeOptions()
                #     # chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                #     # chrome_options.add_argument("--disable-gpu")
                #     # chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
                #     # chrome_options.add_argument('--disable-infobars')
                #     # chrome_options.add_argument("--start-maximized")
                #     chrome_options.add_argument("--headless")
                #     chrome_options.add_argument("--incognito")
                #     # chrome_options.add_argument('--ignore-certificate-errors')
                #     # chrome_options.add_argument('--ignore-ssl-errors')
                #     chrome_options.add_argument("--disable-cache")  # Отключение кэша
                #     chrome_options.add_argument("--disable-cookies")  # Отключение cookies
                #     chrome_options.add_argument(
                #         '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')
                #     s = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
                #     driver = webdriver.Chrome(service=s, options=chrome_options)
                #     # driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                #     #     'source': '''
                #     #         delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                #     #         delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                #     #         delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                #     #   '''
                #     # })
                #     return driver
                # driver = get_chromedriver()
                # driver.get(url[0])
                # cookies = driver.get_cookies()
                # cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                pause_time = random.randint(1, 5)
                proxy = random.choice(proxies)
                proxy_host = proxy[0]
                proxy_port = proxy[1]
                proxy_user = proxy[2]
                proxy_pass = proxy[3]
                # driver.save_screenshot(f'{filename}.png')
                # print(cookies_dict)
                proxi = {
                    'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
                    'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
                }
                try:
                    response = requests.get(url[0], cookies=cookies, headers=headers)  # , proxies=proxi
                except:
                    continue
                data = response.json()

                with open(filename, 'w') as f:
                    json.dump(data, f)
                time.sleep(pause_time)
                print(f"{pause_time}, сохранили {filename}")
            counter += 1


def parsin():
    folders_html = r"c:\DATA\copart\product\*.json"
    files_html = glob.glob(folders_html)
    with open(f'data.csv', "w", newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")

        for i in files_html:
            datas = []

            with open(i, 'r') as f:
                # Загрузить JSON из файла
                data_json = json.load(f)
            print(i)
            'https: // www.copart.com / lot / 43079133 / salvage - 2018 - ford - focus - se - fl - miami - south'
            ln = data_json['data']['lotDetails']['ln']
            url_lot = f"https://www.copart.com/lot/{ln}"
            url_img = data_json['data']['lotDetails']['tims']
            name_lot = data_json['data']['lotDetails']['ld']
            price_bnp = data_json['data']['lotDetails']['bnp']
            odometer_lot = data_json['data']['lotDetails']['orr']
            try:
                drive_lot = data_json['data']['lotDetails']['drv']
            except:
                drive_lot = None
            try:
                engine_type_lot = data_json['data']['lotDetails']['egn']
            except:
                engine_type_lot = None
            try:
                vehicle_type_lot = data_json['data']['lotDetails']['vehTypDesc']
            except:
                vehicle_type_lot = None
            try:
                highlights_lot = data_json['data']['lotDetails']['lcd']
            except:
                highlights_lot = None
            sale_location = data_json['data']['lotDetails']['yn']
            datas = [url_lot, url_img, name_lot, price_bnp, odometer_lot, drive_lot, engine_type_lot, vehicle_type_lot,
                     highlights_lot, sale_location]
            writer.writerow(datas)


if __name__ == '__main__':
    # get_selenium()
    # get_request()
    get_id_ad_and_url()
    get_product()
    parsin()
