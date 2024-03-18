import aiohttp
import asyncio
import aiofiles
from bs4 import BeautifulSoup
import json
import os
import random
from proxi import proxies

cookies = {
    'v': '1687779613_7a9edbc4-e4ec-45a3-8aee-8d9a233b2285_b115594fa9b7229d41139b36cf562f7b',
    'vct': 'en-US-CR8deZlk8B8deZlkSBwdeZlk4R0deZlk4h0deZlk',
    '_csrf': 'hlwBqgGxnyWNdzlUUNdcf3C_',
    'jdv': 't7WOzUb2vHLZtWVVHSk9XJMdN7ua9zR%2FUkXoZtQMDxPlgkBDnOmreue175uoTwe7WLcuJcvxFwz9ShkgfTvhjY%2F6sIoS',
    'prf': 'prodirDistFil%7C%7D',
    'kcan': '0',
    'hzd': "6941bb40-1131-4fc7-b535-92612e669f8b%3A2166961%3Auniprof%3Abrowse_pro%3A2%3ASHANDRIKA'SREALESTATE%2CSTAGING%26",
    '_gid': 'GA1.2.1300049115.1687779615',
    '_gat': '1',
    '_gcl_au': '1.1.221532863.1687779615',
    '_ga_PB0RC2CT7B': 'GS1.1.1687779615.1.0.1687779615.60.0.0',
    '_ga': 'GA1.1.1231471005.1687779615',
    'kucan': '0',
    '_sp_ses.c905': '*',
    '_sp_id.c905': 'f8c599da-021e-473a-9dd6-10883dff5734.1687779616.1.1687779616.1687779616.6b553612-f9e1-4e78-9c02-c589dc514b9e',
    '_uetsid': '37fae580141611eeaf12833da3b0cc3d',
    '_uetvid': '37fafb70141611eeac929344bd6ca4e1',
    'IR_gbd': 'houzz.com',
    'IR_5455': '1687779615686%7C0%7C1687779615686%7C%7C',
    'ln_or': 'eyIzODE1NzE2IjoiZCJ9',
    '_pin_unauth': 'dWlkPU56WTJOV00xWm1NdE1XSXlPUzAwTmpFekxUZzBNVGd0TlRoaU5qSmxOV0ZqTnpnNQ',
    'documentWidth': '878',
    'crossdevicetracking': 'c17a3dc2-e2b6-48d8-90e0-29403f554a3c',
}

headers = {
    'authority': 'www.houzz.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru',
    'cache-control': 'no-cache',
    # 'cookie': "v=1687779613_7a9edbc4-e4ec-45a3-8aee-8d9a233b2285_b115594fa9b7229d41139b36cf562f7b; vct=en-US-CR8deZlk8B8deZlkSBwdeZlk4R0deZlk4h0deZlk; _csrf=hlwBqgGxnyWNdzlUUNdcf3C_; jdv=t7WOzUb2vHLZtWVVHSk9XJMdN7ua9zR%2FUkXoZtQMDxPlgkBDnOmreue175uoTwe7WLcuJcvxFwz9ShkgfTvhjY%2F6sIoS; prf=prodirDistFil%7C%7D; kcan=0; hzd=6941bb40-1131-4fc7-b535-92612e669f8b%3A2166961%3Auniprof%3Abrowse_pro%3A2%3ASHANDRIKA'SREALESTATE%2CSTAGING%26; _gid=GA1.2.1300049115.1687779615; _gat=1; _gcl_au=1.1.221532863.1687779615; _ga_PB0RC2CT7B=GS1.1.1687779615.1.0.1687779615.60.0.0; _ga=GA1.1.1231471005.1687779615; kucan=0; _sp_ses.c905=*; _sp_id.c905=f8c599da-021e-473a-9dd6-10883dff5734.1687779616.1.1687779616.1687779616.6b553612-f9e1-4e78-9c02-c589dc514b9e; _uetsid=37fae580141611eeaf12833da3b0cc3d; _uetvid=37fafb70141611eeac929344bd6ca4e1; IR_gbd=houzz.com; IR_5455=1687779615686%7C0%7C1687779615686%7C%7C; ln_or=eyIzODE1NzE2IjoiZCJ9; _pin_unauth=dWlkPU56WTJOV00xWm1NdE1XSXlPUzAwTmpFekxUZzBNVGd0TlRoaU5qSmxOV0ZqTnpnNQ; documentWidth=878; crossdevicetracking=c17a3dc2-e2b6-48d8-90e0-29403f554a3c",
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


async def get_requests(session, url):
    data_url = []

    group = url.split('/')[-2]
    print(f'Собираем категорию {group}')

    proxy = random.choice(proxies)
    ip, port, user, password = proxy
    proxy_auth_str = f'http://{user}:{password}@{ip}:{port}'

    async with session.get(url, headers=headers, cookies=cookies, proxy=proxy_auth_str) as response:
        src = await response.text()

    soup = BeautifulSoup(src, 'lxml')
    script_json = soup.find('script', type="application/json")
    data_json = json.loads(script_json.string)
    try:
        pagination_total = int(
            data_json['data']['stores']['data']['ViewProfessionalsStore']['data']['paginationSummary']['total'].replace(
                ',', ''))
    except:
        print(f'Нет данных в категории {group}')
        return

    amount_page = pagination_total // 15
    print(f"{pagination_total} а файлов будет {amount_page + 2}")
    coun = 0
    for i in range(1, amount_page + 2):
        if i == 1:
            filename = f"c:\\DATA\\houzz_com\\list\\{group}\\data_{coun}.html"
            if not os.path.exists(filename):
                url_first = url
                try:
                    async with session.get(url_first, headers=headers, cookies=cookies, proxy=proxy_auth_str) as response:
                        response_text = await response.text()
                    async with aiofiles.open(filename, mode='w', encoding='utf-8') as f:
                        await f.write(response_text)
                    async with aiofiles.open('log.txt', 'a') as f:
                        await f.write(f'{url_first}\n')
                except:
                    continue
        elif i > 1:
            coun += 15
            filename = f"c:\\DATA\\houzz_com\\list\\{group}\\data_{coun}.html"
            if not os.path.exists(filename):
                urls = f'{url}?fi={coun}'
                try:
                    async with session.get(urls, headers=headers, cookies=cookies, proxy=proxy_auth_str) as response:
                        response_text = await response.text()
                    async with aiofiles.open(filename, mode='w', encoding='utf-8') as f:
                        await f.write(response_text)
                    async with aiofiles.open('log.txt', 'a') as f:
                        await f.write(f'{urls}\n')
                except:
                    continue
        print(f'Группа {group} осталось {pagination_total - coun} ')

    print(f'Собрали все html {group}**********************************************')


async def main():
    urls = [
        'https://www.houzz.com/professionals/furniture-and-accessories/probr0-bo~t_11802',
        # 'https://www.houzz.com/professionals/universal-design/probr0-bo~t_34260',
        'https://www.houzz.com/professionals/artist-and-artisan/probr0-bo~t_11801',
        'https://www.houzz.com/professionals/agents-and-brokers/probr0-bo~t_11822',
        'https://www.houzz.com/professionals/roofing-and-gutter/probr0-bo~t_11819',
        'https://www.houzz.com/professionals/appliances/probr0-bo~t_11810',
        'https://www.houzz.com/professionals/electrical-contractors/probr0-bo~t_11818',
        'https://www.houzz.com/professionals/home-media/probr0-bo~t_11787',
        'https://www.houzz.com/professionals/hvac-contractors/probr0-bo~t_11814',
        'https://www.houzz.com/professionals/plumbing-contractors/probr0-bo~t_11817',
        'https://www.houzz.com/professionals/septic-tanks-and-systems/probr0-bo~t_11815',
        'https://www.houzz.com/professionals/solar-energy-contractors/probr0-bo~t_11816',
        'https://www.houzz.com/professionals/carpet-cleaners/probr0-bo~t_27201',
        'https://www.houzz.com/professionals/chimney-cleaners/probr0-bo~t_27200',
        'https://www.houzz.com/professionals/exterior-cleaners/probr0-bo~t_27202',
        'https://www.houzz.com/professionals/house-cleaners/probr0-bo~t_27205',
        'https://www.houzz.com/professionals/rubbish-removal/probr0-bo~t_11820',
        'https://www.houzz.com/professionals/pest-control/probr0-bo~t_27207',
        'https://www.houzz.com/professionals/window-cleaners/probr0-bo~t_27209'
    ]
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            tasks.append(asyncio.create_task(get_requests(session, url)))
        await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
