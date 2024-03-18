import aiohttp
import asyncio
import os
import csv
cookies = {
    'v': '1685342053_398c990a-5e3a-4fc6-9a54-2e1738a2b82c_1fcb553b0f2c8f94c21109cd9040f041',
    '_csrf': 'tQX_Zde7kKPolFIfWRE8pxIL',
    'jdv': 't7WOzUb2vHLZtWVVHSk%2BXJMaN7ua9zR%2FUkXpY9RZDRS20RNAnLz7eLbg7JysQQXvVbYtdZ6jEQ%2FwTRwkfzK7it%2BquIxC',
    'prf': 'prodirDistFil%7C%7D',
    'cced': '1',
    'xauth': '1685342062',
    'v2': '1685342062_e996f727-364e-4c7d-be7a-10a74a80ac59_cb26317f415693fb03b109d615ea09e4',
    'g_state': '{"i_p":1685349277940,"i_l":1}',
    'ppclk': 'organicUId%3D30338175%2Cpage%3D2',
    'vct': 'es-ES-Bh4oS3RkOR8oS3RkTBwoS3Rk6R0oS3Rk6h0oS3Rk',
    'documentWidth': '1122',
    'kcan': '0',
    'hzd': '17ce7623-0051-4b44-aa1b-b6ca149842b5%3A%3A%3A%3A%3AArquitectosPonteencontactoconp',
}

headers = {
    'authority': 'www.houzz.es',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'no-cache',
    # 'cookie': 'v=1685342053_398c990a-5e3a-4fc6-9a54-2e1738a2b82c_1fcb553b0f2c8f94c21109cd9040f041; _csrf=tQX_Zde7kKPolFIfWRE8pxIL; jdv=t7WOzUb2vHLZtWVVHSk%2BXJMaN7ua9zR%2FUkXpY9RZDRS20RNAnLz7eLbg7JysQQXvVbYtdZ6jEQ%2FwTRwkfzK7it%2BquIxC; prf=prodirDistFil%7C%7D; cced=1; xauth=1685342062; v2=1685342062_e996f727-364e-4c7d-be7a-10a74a80ac59_cb26317f415693fb03b109d615ea09e4; g_state={"i_p":1685349277940,"i_l":1}; ppclk=organicUId%3D30338175%2Cpage%3D2; vct=es-ES-Bh4oS3RkOR8oS3RkTBwoS3Rk6R0oS3Rk6h0oS3Rk; documentWidth=1122; kcan=0; hzd=17ce7623-0051-4b44-aa1b-b6ca149842b5%3A%3A%3A%3A%3AArquitectosPonteencontactoconp',
    'dnt': '1',
    'pragma': 'no-cache',
    'referer': 'https://www.houzz.es/professionals/arquitectos/probr0-bo~t_17749',
    'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
}

async def download(url, counter):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, cookies=cookies, headers=headers) as response:
                content = await response.text()
                filename = f"c:\\data_houzz_es\\list\\data_{counter}.html"
                if not os.path.isfile(filename):
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(content)
                    # print(f"Saved {url} to {filename}")
                else:
                    print(f"File {filename} already exists")
        except Exception as e:
            print(f"Error downloading {url}: {e}")


async def main():
    counter = 0
    limit = 100
    delay = 10

    with open("data.csv") as f:
        reader = csv.reader(f)
        urls = [row[0] for row in reader]

    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            tasks.append(download(url, counter))
            counter += 1
            if counter % limit == 0:
                await asyncio.gather(*tasks)
                tasks = []
                print(f"Waiting for {delay} seconds...")
                await asyncio.sleep(delay)
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
