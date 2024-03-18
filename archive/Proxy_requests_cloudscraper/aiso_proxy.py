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

