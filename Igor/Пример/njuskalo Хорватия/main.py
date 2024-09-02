# import pytesseract
# import io
# import base64
# import json
# from PIL import Image
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from threading import Lock
import threading
import requests
import datetime
import random
import os
import re

links_file = f'links_file.txt'
lock = Lock()
RED = "\033[31m"
RESET = "\033[0m"

def write_data(data, filename):
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(f"{data}\n")

def get_url(url):
    counter_error = 0

    print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Получение страницы {url}.')

    ua = UserAgent()

    proxies = [line.strip() for line in open('C:\\proxy\\1000 ip.txt', 'r', encoding='utf-8')]

    while proxies:
        if len(proxies) > 0:
            proxy = random.choice(proxies)
        else:
            print("Список прокси пуст")
            return None

        proxies_dict = {
            'http': proxy,
            'https': proxy,
        }

        try:
            cookies = {
                'nuka-fp': 'bbbd578a-b1d0-4d13-babd-70660e4f3ca4',
                'login_2fa': 'bbbd578a-b1d0-4d13-babd-70660e4f3ca4',
                '__uzma': 'e6b0988c-48a9-4708-b4c3-ced17d91d04e',
                '__uzmb': '1710019936',
                '__uzme': '2351',
                'njuskalo_privacy_policy': '11',
                'didomi_token': 'eyJ1c2VyX2lkIjoiMThlMjUyMTctNDdhMC02OTAxLTk4OTAtZDgyNjQ4N2ViMDVhIiwiY3JlYXRlZCI6IjIwMjQtMDMtMDlUMjE6MzI6MTMuMzA2WiIsInVwZGF0ZWQiOiIyMDI0LTAzLTA5VDIxOjMyOjE2Ljk2OVoiLCJ2ZW5kb3JzIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiYW1hem9uIiwiYzppbnRvd293aW4tcWF6dDV0R2kiLCJjOmRpZG9taSIsImM6aG90amFyIiwiYzpuZXctcmVsaWMiLCJjOmNvbW0xMDAiLCJjOmxpdmVjaGF0IiwiYzpib29raXRzaC1LYjhuYkFEaCIsImM6Y29tbTEwMHZpLXdkbU1tNEo2IiwiYzpib29raXRsYS1NYVJnZ21QTiIsImM6ZG90bWV0cmljLWk4YnFnWkNMIiwiYzpkb3RtZXRyaWMtZ2IyZmpLQ0oiLCJjOmRvdG1ldHJpYy1yakFoZXBSZyIsImM6c3R5cmlhLXFoVWNra1plIiwiYzppc2xvbmxpbmUtRjlHQmdwUWgiLCJjOnhpdGktQjN3Ym5KS1IiLCJjOmV0YXJnZXQtV3dFakFRM0ciLCJjOmdvb2dsZWFuYS0yM2RkY3JEaCIsImM6bnVrYXJlY29tLXdra0JkcU04IiwiYzpnb29nbGVhbmEtNFRYbkppZ1IiLCJjOnBpYW5vaHlici1SM1ZLQzJyNCIsImM6bWlkYXMtZUJuVEdYTEYiLCJjOnBpbnRlcmVzdCIsImM6dGVsdW0ta3c0RG1wUGsiLCJjOmRvdG1ldHJpYy1NOTd0ZExKWCIsImM6Z2VtaXVzc2EtbWNraVFhbksiLCJjOmluc3VyYWRzLUpnQ0Y2cG1YIiwiYzpob3RqYXItWkxQTGV4VmIiLCJjOmdvb2dsZWFuYS04aUhHUkN0VSIsImM6b3B0aW1heG1lLU5IWGVRY0NrIiwiYzpibG9ja3Rocm91LVlMN3daVWZWIiwiYzpkaWRvbWktbmtHakdkeGoiLCJjOnNtYXJ0YWRzZS03V004WGdURiIsImM6Y3JpdGVvc2EtZ2pwY3JtZ0IiLCJjOmdvb2dsZWFkdi1aWjllN1lkaSIsImM6bmp1c2thbG9uLUFZY05OYWl3IiwiYzpiaWRzd2l0Y2gtRXRiN0xhNFIiLCJjOmFkYWdpby1GWWdmNHdSRCIsImM6bmp1c2thbG9uLUE3Y1BWZUVhIiwiYzphbWF6b25hZC1DMnluTlVuOSIsImM6eWFob29hZGUtbVJIUWtobVUiLCJjOm1kcHJpbWlzLVdNWkFSbXc2IiwiYzphbWF6b24tTDg0dEpReDQiXX0sInB1cnBvc2VzIjp7ImVuYWJsZWQiOlsib2dsYXNpdmFjay1RNEQ5Ym1URyIsImF1ZGllbmNlbS1oSnhhZUdyUiIsImFuYWx5dGljcy14R0h4R3BUTCIsImRldmljZV9jaGFyYWN0ZXJpc3RpY3MiLCJnZW9sb2NhdGlvbl9kYXRhIl19LCJ2ZW5kb3JzX2xpIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiYzptaWRhcy1lQm5UR1hMRiJdfSwicHVycG9zZXNfbGkiOnsiZW5hYmxlZCI6WyJvZ2xhc2l2YWNrLVE0RDlibVRHIl19LCJ2ZXJzaW9uIjoyLCJhYyI6IkFrdUFFQUZrQkpZQS5Ba3VBRUFGa0JKWUEifQ==',
                'euconsent-v2': 'CP7NIEAP7NIEAAHABBENAqEsAP_gAEPgAAAAg1NX_H__bW9r8Xr3aft0eY1P99j77sQxBhfJE-4FzLvW_JwXx2ExNA36tqIKmRIEu3bBIQFlHJDUTVigaogVryDMakWcgTNKJ6BkiFMRc2dYCF5vmQtj-QKY5vp9d3dx2D-t_dv83dzyz8VHn3e5_2e0eJCdA58tDfv9bROb-9IPd_58v4v0_F_rk2_eT1l_tevp7B8uft87_XU-9_fff78AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEQaoaIACIAFAAXAA4AD4AKAAqABcADgAHgAQAAkgBcAGUANAA1AB4AD8AIgARwAmABQgCkAKYAVYAtgC6AGIAMwAaAA3gB6AD4AH4AQgAhoBEAESAI4ASwAmgBOACjAGAAMOAZQBlgDNAGiANkAckA5wDogHcAd4A9gB8QD7AP2Af4CAQEHAQgAiIBFICLAIwARqAjgCOgEiAJKASkAmgBPwCgwFQAVEAq4BYgC5gF1gLyAvQBfQDFAGiANeAbQA3ABxADjgHSAOoAdsA9oB9gD-gH_AQgAiYBF4CPYEiASKAlYBMQCZQE2gJ2AUPAo8CkQFJgKaAU-AqGBUgFSgKsAVyArsBYUCxALFAWiAtSBbAFswLcAt0BcAC5AF0ALtAXfAvIC8wF9AL_AYIAwYBhoDEAGLAMeAZDAyMDJIGTAZOAyoBlgDMwGcgM8AaIA0YBpoDUwGqwNXA1kBrwDaAG2QNuA2-BuQG6gOCAcWA48BycDlgOXAc6A58B4oDx4HkgeUA9oB8UD5APlAfXA-0D7oH7AfuA_sB_wEAQICAQMAgeBBECCYEGAINgQhAhQBCuCFoIXgQzghyCHUEPAQ9Ah-BFMCMAEaQI3gR0Aj2BH0CP4EhAJFASNgkgCSUEmASZglQCVIEsAJZwS3BLiCXQJdgS-gmACYIEwwJiwTMBM4CagE2IJtgm5BN4E3wJwwTlBOYCdIE64J2gncBPACeYQagAR0AEBMgA.f_wACHwAAAAA',
                '_gcl_au': '1.1.1774144976.1710019937',
                'nuka-recommender-fp': 'bbbd578a-b1d0-4d13-babd-70660e4f3ca4',
                'df_uid': '820e458e-ad71-4c64-bd13-9a14140a4945',
                'njuskalo_adblock_detected': 'true',
                'PHPSESSID': '0c3e0bd4d0a2300b24a197e0f84004d1',
                '__uzmc': '455794351508',
                '__uzmd': '1710030646',
            }

            headers = {
                'authority': 'www.njuskalo.hr',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
                'cache-control': 'max-age=0',
                # 'cookie': 'nuka-fp=bbbd578a-b1d0-4d13-babd-70660e4f3ca4; login_2fa=bbbd578a-b1d0-4d13-babd-70660e4f3ca4; __uzma=e6b0988c-48a9-4708-b4c3-ced17d91d04e; __uzmb=1710019936; __uzme=2351; njuskalo_privacy_policy=11; didomi_token=eyJ1c2VyX2lkIjoiMThlMjUyMTctNDdhMC02OTAxLTk4OTAtZDgyNjQ4N2ViMDVhIiwiY3JlYXRlZCI6IjIwMjQtMDMtMDlUMjE6MzI6MTMuMzA2WiIsInVwZGF0ZWQiOiIyMDI0LTAzLTA5VDIxOjMyOjE2Ljk2OVoiLCJ2ZW5kb3JzIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiYW1hem9uIiwiYzppbnRvd293aW4tcWF6dDV0R2kiLCJjOmRpZG9taSIsImM6aG90amFyIiwiYzpuZXctcmVsaWMiLCJjOmNvbW0xMDAiLCJjOmxpdmVjaGF0IiwiYzpib29raXRzaC1LYjhuYkFEaCIsImM6Y29tbTEwMHZpLXdkbU1tNEo2IiwiYzpib29raXRsYS1NYVJnZ21QTiIsImM6ZG90bWV0cmljLWk4YnFnWkNMIiwiYzpkb3RtZXRyaWMtZ2IyZmpLQ0oiLCJjOmRvdG1ldHJpYy1yakFoZXBSZyIsImM6c3R5cmlhLXFoVWNra1plIiwiYzppc2xvbmxpbmUtRjlHQmdwUWgiLCJjOnhpdGktQjN3Ym5KS1IiLCJjOmV0YXJnZXQtV3dFakFRM0ciLCJjOmdvb2dsZWFuYS0yM2RkY3JEaCIsImM6bnVrYXJlY29tLXdra0JkcU04IiwiYzpnb29nbGVhbmEtNFRYbkppZ1IiLCJjOnBpYW5vaHlici1SM1ZLQzJyNCIsImM6bWlkYXMtZUJuVEdYTEYiLCJjOnBpbnRlcmVzdCIsImM6dGVsdW0ta3c0RG1wUGsiLCJjOmRvdG1ldHJpYy1NOTd0ZExKWCIsImM6Z2VtaXVzc2EtbWNraVFhbksiLCJjOmluc3VyYWRzLUpnQ0Y2cG1YIiwiYzpob3RqYXItWkxQTGV4VmIiLCJjOmdvb2dsZWFuYS04aUhHUkN0VSIsImM6b3B0aW1heG1lLU5IWGVRY0NrIiwiYzpibG9ja3Rocm91LVlMN3daVWZWIiwiYzpkaWRvbWktbmtHakdkeGoiLCJjOnNtYXJ0YWRzZS03V004WGdURiIsImM6Y3JpdGVvc2EtZ2pwY3JtZ0IiLCJjOmdvb2dsZWFkdi1aWjllN1lkaSIsImM6bmp1c2thbG9uLUFZY05OYWl3IiwiYzpiaWRzd2l0Y2gtRXRiN0xhNFIiLCJjOmFkYWdpby1GWWdmNHdSRCIsImM6bmp1c2thbG9uLUE3Y1BWZUVhIiwiYzphbWF6b25hZC1DMnluTlVuOSIsImM6eWFob29hZGUtbVJIUWtobVUiLCJjOm1kcHJpbWlzLVdNWkFSbXc2IiwiYzphbWF6b24tTDg0dEpReDQiXX0sInB1cnBvc2VzIjp7ImVuYWJsZWQiOlsib2dsYXNpdmFjay1RNEQ5Ym1URyIsImF1ZGllbmNlbS1oSnhhZUdyUiIsImFuYWx5dGljcy14R0h4R3BUTCIsImRldmljZV9jaGFyYWN0ZXJpc3RpY3MiLCJnZW9sb2NhdGlvbl9kYXRhIl19LCJ2ZW5kb3JzX2xpIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiYzptaWRhcy1lQm5UR1hMRiJdfSwicHVycG9zZXNfbGkiOnsiZW5hYmxlZCI6WyJvZ2xhc2l2YWNrLVE0RDlibVRHIl19LCJ2ZXJzaW9uIjoyLCJhYyI6IkFrdUFFQUZrQkpZQS5Ba3VBRUFGa0JKWUEifQ==; euconsent-v2=CP7NIEAP7NIEAAHABBENAqEsAP_gAEPgAAAAg1NX_H__bW9r8Xr3aft0eY1P99j77sQxBhfJE-4FzLvW_JwXx2ExNA36tqIKmRIEu3bBIQFlHJDUTVigaogVryDMakWcgTNKJ6BkiFMRc2dYCF5vmQtj-QKY5vp9d3dx2D-t_dv83dzyz8VHn3e5_2e0eJCdA58tDfv9bROb-9IPd_58v4v0_F_rk2_eT1l_tevp7B8uft87_XU-9_fff78AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEQaoaIACIAFAAXAA4AD4AKAAqABcADgAHgAQAAkgBcAGUANAA1AB4AD8AIgARwAmABQgCkAKYAVYAtgC6AGIAMwAaAA3gB6AD4AH4AQgAhoBEAESAI4ASwAmgBOACjAGAAMOAZQBlgDNAGiANkAckA5wDogHcAd4A9gB8QD7AP2Af4CAQEHAQgAiIBFICLAIwARqAjgCOgEiAJKASkAmgBPwCgwFQAVEAq4BYgC5gF1gLyAvQBfQDFAGiANeAbQA3ABxADjgHSAOoAdsA9oB9gD-gH_AQgAiYBF4CPYEiASKAlYBMQCZQE2gJ2AUPAo8CkQFJgKaAU-AqGBUgFSgKsAVyArsBYUCxALFAWiAtSBbAFswLcAt0BcAC5AF0ALtAXfAvIC8wF9AL_AYIAwYBhoDEAGLAMeAZDAyMDJIGTAZOAyoBlgDMwGcgM8AaIA0YBpoDUwGqwNXA1kBrwDaAG2QNuA2-BuQG6gOCAcWA48BycDlgOXAc6A58B4oDx4HkgeUA9oB8UD5APlAfXA-0D7oH7AfuA_sB_wEAQICAQMAgeBBECCYEGAINgQhAhQBCuCFoIXgQzghyCHUEPAQ9Ah-BFMCMAEaQI3gR0Aj2BH0CP4EhAJFASNgkgCSUEmASZglQCVIEsAJZwS3BLiCXQJdgS-gmACYIEwwJiwTMBM4CagE2IJtgm5BN4E3wJwwTlBOYCdIE64J2gncBPACeYQagAR0AEBMgA.f_wACHwAAAAA; _gcl_au=1.1.1774144976.1710019937; nuka-recommender-fp=bbbd578a-b1d0-4d13-babd-70660e4f3ca4; df_uid=820e458e-ad71-4c64-bd13-9a14140a4945; njuskalo_adblock_detected=true; PHPSESSID=0c3e0bd4d0a2300b24a197e0f84004d1; __uzmc=455794351508; __uzmd=1710030646',
                'referer': 'https://www.njuskalo.hr/auti?page=6',
                'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Microsoft Edge";v="122"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': ua.random,
            }

            response = requests.get(
                url=url,
                timeout=60,
                headers=headers,
                proxies=proxies_dict,
                # allow_redirects=True,
            )

            # if response.history:
            #     print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Запрос был перенаправлен.')
            #     return 'Редирект'
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup
            elif response.status_code == 403:
                print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Код ошибки 403. Сайт нас подрезал.')
                proxies.remove(proxy)
                print(proxy)
                print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Осталось прокси {len(proxies)}')
                counter_error += 1
                if counter_error == 10:
                    print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Перезапуск, нас подрезали.')
                    return None
            else:
                return None
        except requests.exceptions.TooManyRedirects:
            print("Произошла ошибка: Exceeded 30 redirects. Пропуск.")
            return 'Редирект'
        except (requests.exceptions.ProxyError, requests.exceptions.Timeout):
            proxies.remove(proxy)
            print(proxy)
            print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Осталось прокси {len(proxies)}')
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            continue

    return None

def get_info(url, filename, links_counter_file, thread_id, lock):
    print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Обрабатывается категория {url} | (Поток -> {thread_id})')
    print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Получение следующей страницы | (Поток -> {thread_id})')

    with lock:
        soup = get_url(url=url)

    if soup == 'Редирект':
        return None

    if soup is None:
        return url
    
    next_page_link = None

    for a in soup.find_all('a', href=True):
        if a.find('i', class_='fa fa-angle-right'):
            next_page_link = f"https://www.economicos.cl{a['href']}"
            print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Следующая страница - {next_page_link} | (Поток -> {thread_id})')
            break

    links = set()

    divs = soup.find_all('div', {'class': 'result row-fluid'})
    for div in divs:
        a_tag = div.find('a')
        if a_tag is not None:
            link = f"http://www.economicos.cl{a_tag['href']}"
            if "INSERT_RANDOM_NUMBER_HERE" not in link:
                links.add(link)

    with lock:
        if os.path.exists(links_file):
            with open(links_file, 'r') as file:
                existing_links = set(file.read().splitlines())
            links.difference_update(existing_links)
            
    # if len(links) == 0:
    #     return None

    for link in links:
        print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Обрабатывается объявление {link}')

        with lock:
            soup = get_url(link)

        if soup == 'Редирект':
            continue

        if soup is None:
            continue
        
        location = None
        phone_numbers = set()

        phone_element = soup.find('strong', {'id': 'phone'})
        if phone_element:
            phones = phone_element.text.strip().split(',')
            for phone in phones:
                phone_number = re.sub(r'\D', '', phone.strip())
                if phone_number and len(phone_number) >= 7:
                    phone_numbers.add(phone_number)

            location_element = soup.find('div', {'class': 'cont_tit_detalle_f'})
            if location_element:
                h3_element = location_element.find('h3')
                if h3_element:
                    location = h3_element.text.strip().replace('\n', '').replace(';', ',').strip()
        
        print(RED,f'{link}\nНомера - {phone_numbers}\nЛокация - {location}',RESET)

        if location and phone_numbers:
            links_count = 1
            
            if os.path.exists(links_counter_file):
                with open(links_counter_file, 'r') as f:
                    total_links_count = int(f.read().strip())
                    links_count += total_links_count
            
            with open(links_counter_file, 'w') as f:
                f.write(str(links_count))
                
            for phone_number in phone_numbers:
                data = f'{phone_number};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{link}'
                print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - {data} | (Поток -> {thread_id})')
                write_data(data=data, filename=filename)
        else:
            print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Номера телефонов или местоположение не найдены | (Поток -> {thread_id})')

        with lock:
            with open(links_file, 'a') as file:
                file.write(link + '\n')
    if next_page_link:
        return next_page_link
    else:
        return None

def main_thread(url, thread_id, lock):
    page_file = f'page_{thread_id}.txt'
    filename = f'Чили - economicos_{thread_id}.csv'
    links_counter_file = f'links_counter_{thread_id}.txt'

    if os.path.exists(page_file):
        with open(page_file, 'r', encoding='utf-8') as f:
            url = f.read().strip()

    while True:
        next_page_link = get_info(url=url, filename=filename, links_counter_file=links_counter_file, thread_id=thread_id, lock=lock)

        if next_page_link:
            url = next_page_link
            with open(page_file, 'w', encoding='utf-8') as f:
                f.write(url)
            continue
        else:
            break

def main():
    urls = open('category.txt', 'r', encoding='utf-8').read().splitlines()
    # threads = []
    # lock = Lock()

    # for i, url in enumerate(urls):
    #     thread = threading.Thread(target=main_thread, args=(url, i, lock))
    #     threads.append(thread)
    #     thread.start()

    # for thread in threads:
    #     thread.join()

    for url in urls:
        soup = get_url(url)

        open('index.html', 'w', encoding='utf-8').write(soup.prettify())

        next_page_link = None

        pagination_ul = soup.find('ul', class_='Pagination-items cf')
        print(pagination_ul)
        if pagination_ul:
            # Внутри найденного <ul> ищем элемент <li> с классом, содержащим "Pagination-item--next" и наличием атрибута data-href
            next_item = pagination_ul.find(lambda tag: tag.name == 'li' and 'Pagination-item--next' in tag.get('class', []) and tag.has_attr('data-href'))
            
            # Если такой элемент найден, извлекаем значение атрибута data-href
            if next_item:
                next_page_link = next_item.find('button')['data-href']

        # Выводим найденную ссылку на следующую страницу
        print(next_page_link)

    #     links = set()

    #     divs = soup.find_all('div', {'class': 'result row-fluid'})
    #     for div in divs:
    #         a_tag = div.find('a')
    #         if a_tag is not None:
    #             link = f"http://www.economicos.cl{a_tag['href']}"
    #             if "INSERT_RANDOM_NUMBER_HERE" not in link:
    #                 links.add(link)
        
    #     print(len(links))

    #     for link in links:
    #         soup = get_url(link)

    #         location = None
    #         phone_numbers = set()

    #         phone_element = soup.find('strong', {'id': 'phone'})
    #         if phone_element:
    #             phones = phone_element.text.strip().split(',')
    #             for phone in phones:
    #                 phone_number = re.sub(r'\D', '', phone.strip())
    #                 if phone_number and len(phone_number) >= 7:
    #                     phone_numbers.add(phone_number)

    #             location_element = soup.find('div', {'class': 'cont_tit_detalle_f'})
    #             if location_element:
    #                 h3_element = location_element.find('h3')
    #                 if h3_element:
    #                     location = h3_element.text.replace('\n', '').strip()
            
    #         print(RED,f'{link}\nНомера - {phone_numbers}\nЛокация - {location}',RESET)
    #         break

if __name__ == '__main__':
    main()