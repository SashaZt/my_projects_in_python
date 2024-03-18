import aiohttp
import asyncio
import os
import csv
import random
import re
from  proxi import proxy_login, proxy_pass, proxy_list
cookies = {
    'ak_bmsc': 'EA9961D4BA849D3AC4CB97CC1C162EA6~000000000000000000000000000000~YAAQDQxAFw0pm9uIAQAAMY6F3RRnVuXFv4jC/DzpcHz8wr4R5Jtr5VTNvGrch9m1g/NzHfRG3zxgATE+LCELn1HESJumYUgLV9nECNF7wGzlRLAhrc7U4P2CQXAVXjEUEemBowLkRk6umFmr/GgGoD9TswWMtSx6mAxUJTuk4DZ4YxEr2ebl7no7YGAWMv5Jeno0qlyI+5m4+JXttGPtupH6rkFwtL2JckEUkKklgQuFAo9jJeZVN+bUhpZ0njZCWWduOGZHr4/AYqb52LGMb5T4q3tdOeXCKGCCdIsupUJTsa6VLSwPyyFURrgns+T/kHnkJMHDTUBcOAtZmhNz1AotifjdjYN+HOJ5ddKwNXwdBgvL3SOiK/oWvCvtC7pZTo/TAiLhrq53',
    'bm_mi': '358A0D18C4DAD9BFA09771FC5AB403C4~YAAQDQxAF60wnNuIAQAAv4GJ3RRjWk57jfsblbuIKwMwsO5DBEnts97/tCHs4oTJ2WG9etYkQA+UjHbplreoaacyd11aa1J1bpbf41cbq3FZ2vpr4Q/tjEIvyonyYO//NYGCkRFufc1CSay0el9XXBXkS30kehveHX2xwsTNDFwJxXI+ffwIxDVWLQv6lypazcpvnlAPpHTPRSg+UrLQ6Zgmw5AsbJF139jLNlOaozuvPJzaViygYhHFnG4QM+fLp8G7sH1zUpQLFAx0QUoWSJEqSb/g6ow09hE1qOBnnIVWU7KCjScTzrMQfg9otIgGWq6AWUEcogaJ9EyWIxf9p9X8enHw~1',
    'bm_sv': '8D7D22C834C4108B2E3B28CCD234DE6C~YAAQDQxAF64wnNuIAQAAv4GJ3RS2BqJNjwW50vYdaE7tC3qz6poW/tZglurMfsps6OSDO6k7t6/pNCtK7SH+GEpHXhoogIHaiTsM/wRXxP0kCFBVFkLwjcjfRizsE+aP9L2rJnNhCfW0Tz77ZfYidkFcSiVjCF5wYs+cFNKDdbfXdrLYvN8GRBlrivyyZsaJlRHqBBEbxX5HRizu8FNh3qJgyGWMk4xkxbD5DlCkurmyMXfNtRdPy51QfQSfAI4=~1',
}

headers = {
    'authority': 'www.tesla.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'no-cache',
    # 'cookie': 'ak_bmsc=EA9961D4BA849D3AC4CB97CC1C162EA6~000000000000000000000000000000~YAAQDQxAFw0pm9uIAQAAMY6F3RRnVuXFv4jC/DzpcHz8wr4R5Jtr5VTNvGrch9m1g/NzHfRG3zxgATE+LCELn1HESJumYUgLV9nECNF7wGzlRLAhrc7U4P2CQXAVXjEUEemBowLkRk6umFmr/GgGoD9TswWMtSx6mAxUJTuk4DZ4YxEr2ebl7no7YGAWMv5Jeno0qlyI+5m4+JXttGPtupH6rkFwtL2JckEUkKklgQuFAo9jJeZVN+bUhpZ0njZCWWduOGZHr4/AYqb52LGMb5T4q3tdOeXCKGCCdIsupUJTsa6VLSwPyyFURrgns+T/kHnkJMHDTUBcOAtZmhNz1AotifjdjYN+HOJ5ddKwNXwdBgvL3SOiK/oWvCvtC7pZTo/TAiLhrq53; bm_mi=358A0D18C4DAD9BFA09771FC5AB403C4~YAAQDQxAF60wnNuIAQAAv4GJ3RRjWk57jfsblbuIKwMwsO5DBEnts97/tCHs4oTJ2WG9etYkQA+UjHbplreoaacyd11aa1J1bpbf41cbq3FZ2vpr4Q/tjEIvyonyYO//NYGCkRFufc1CSay0el9XXBXkS30kehveHX2xwsTNDFwJxXI+ffwIxDVWLQv6lypazcpvnlAPpHTPRSg+UrLQ6Zgmw5AsbJF139jLNlOaozuvPJzaViygYhHFnG4QM+fLp8G7sH1zUpQLFAx0QUoWSJEqSb/g6ow09hE1qOBnnIVWU7KCjScTzrMQfg9otIgGWq6AWUEcogaJ9EyWIxf9p9X8enHw~1; bm_sv=8D7D22C834C4108B2E3B28CCD234DE6C~YAAQDQxAF64wnNuIAQAAv4GJ3RS2BqJNjwW50vYdaE7tC3qz6poW/tZglurMfsps6OSDO6k7t6/pNCtK7SH+GEpHXhoogIHaiTsM/wRXxP0kCFBVFkLwjcjfRizsE+aP9L2rJnNhCfW0Tz77ZfYidkFcSiVjCF5wYs+cFNKDdbfXdrLYvN8GRBlrivyyZsaJlRHqBBEbxX5HRizu8FNh3qJgyGWMk4xkxbD5DlCkurmyMXfNtRdPy51QfQSfAI4=~1',
    'dnt': '1',
    'pragma': 'no-cache',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}

# proxy = f'http://{random.choice(proxy_list)}'
ip, port = random.choice(proxy_list)
proxy = f'http://{ip}:{port}'
proxy_auth = aiohttp.BasicAuth(proxy_login, proxy_pass) #Логин и пароль

async def download(url, counter, group):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, cookies=cookies, headers=headers, proxy=proxy, proxy_auth=proxy_auth) as response: #, proxy=proxy, proxy_auth=proxy_auth
                print(proxy, proxy_auth)
                content = await response.text()
                filename = f"c:\\DATA\\tesla\\data_{counter}.html"
                if not os.path.isfile(filename):
                    with open(filename, "w", encoding="latin1") as f:
                        f.write(content)
                    # print(f"Saved {url} to {filename}")
                else:
                    print(f"File {filename} already exists")
        except Exception as e:
            print(f"Error downloading {url}: {e}")


async def main():
    """
    counter - счетчик начало отсчета
    limit - лимит запросов за один проход
    delay - пауза в секундах до следующего захода, random.randint(10,30) случайная пауза от 10 до 30 сек
    """
    counter = 0
    limit = 100
    delay = 5

    csv_folder = "c:\\scrap_tutorial-master\\tesla\\url\\"  # Путь к папке с CSV файлами
    csv_files = [file for file in os.listdir(csv_folder) if file.endswith(".csv")]

    async with aiohttp.ClientSession() as session:
        tasks = []
        for csv_file in csv_files:
            with open(os.path.join(csv_folder, csv_file), encoding='latin-1') as f:
                reader = csv.reader(f)
                urls = [row[0] for row in reader]

            group = re.findall(r"([^\\/:*?\"<>|]+)\.csv", csv_file)[0]  # Извлекаем группу из имени файла

            for url in urls:
                # delay = random.randint(10,30)

                tasks.append(download(url, counter, group))
                counter += 1
                if counter % limit == 0:
                    await asyncio.gather(*tasks)
                    tasks = []
                    print(f"Waiting for {delay} seconds... {counter}")
                    await asyncio.sleep(delay)
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
