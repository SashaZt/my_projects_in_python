cookies = {
    'cid': '149905558730700005005275127777618119701',
    'evoauth': 'wb52a1c0a48654244bc20f4f10d96b6b9',
    '_ga': 'GA1.1.834139681.1693817061',
    '_gcl_au': '1.1.788596630.1693817061',
    '_ga_T7S2G9Q21Q': 'GS1.1.1693817060.1.0.1693817062.0.0.0',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru',
    'cache-control': 'max-age=0',
    # 'cookie': 'cid=149905558730700005005275127777618119701; csrf_token_company_site=6d036671fbdd4a97a70b683eae812906; evoauth=wb52a1c0a48654244bc20f4f10d96b6b9; _ga=GA1.1.834139681.1693817061; _gcl_au=1.1.788596630.1693817061; _ga_T7S2G9Q21Q=GS1.1.1693817060.1.0.1693817062.0.0.0',
    'dnt': '1',
    'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
}
headers['Cookie'] = '; '.join([f'{k}={v}' for k, v in cookies.items()])