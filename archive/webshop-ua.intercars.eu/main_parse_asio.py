import os
import csv
import re
import glob
import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup


async def download_image(session, img_url, file_path):
    async with session.get(img_url) as response:
        img_data = await response.read()
        with open(file_path, 'wb') as file_img:
            file_img.write(img_data)


async def process_file(session, item, writer):
    filename_csv = os.path.basename(item)
    filename_csv = os.path.splitext(filename_csv)[0].replace("_", " ")

    with open(item, encoding="utf-8") as file:
        src = file.read()

    soup = BeautifulSoup(src, 'lxml')

    try:
        name_product = soup.find('span', attrs={'class': 'active_filters_span'}).text.replace("\n", "").strip()
    except:
        name_product = filename_csv
    selectors_img = [
        ('a', {"data-gc-onclick": "dyn-gallery"}),
        ('img', {"id": "article-image-thumb"}),
        ('a', {"id": "btn_gallery_30"}),

    ]
    script_div_img = None
    for tag, attributes in selectors_img:
        try:
            if 'data-dyngalposstring' in attributes:
                script_div_img = soup.find(tag, attributes['data-dyngalposstring'])
            else:
                script_div_img = soup.find(tag, attributes)
            break  # Если нашли совпадение, выходим из цикла
        except:
            continue  # Если не нашли, продолжаем проверку следующего селектора
    # try:
    #     script_div = soup.find('a', attrs={'data-gc-onclick': 'dyn-gallery'})['data-dyngalposstring']
    # except:
    #     script_div = soup.find('img', attrs={'id': 'article-image-thumb'})['data-dyngalposstring']
    pattern = re.compile(r"'src': '(.+?)',")
    if script_div_img is not None:
        result = pattern.findall(str(script_div_img))
    else:
        result = []
    # print(result)

    """Получение данных"""
    """Проверка нескольких условий"""
    selectors = [
        ('div', {"class": "col-xs-12 p-l-2 p-r-2 f-12 text-center"}),
        ('span', {"id": "name_30"}),
        ('h1', {"class": "item-title word-break-anywhere hidden-xs"})
    ]

    full_name = None

    for tag, attributes in selectors:
        try:
            element = soup.find(tag, attributes)
            if element and element.text.strip():  # проверяем, что текст присутствует и он не пустой
                full_name = element.text.replace("\n", "").strip()
                break  # Если нашли совпадение, выходим из цикла
        except:
            continue  # Если не нашли, продолжаем проверку следующего селектора

    # Если full_name остался None, значит ни одно из условий не сработало
    details_card_div = soup.find("div", {"id": "details_card"})
    barcode = None
    try:
        divs = details_card_div.find_all("div", class_="clearfix flexcard p-l-2 p-r-2")
        pattern = re.compile(r"Штрих-ко.*?(\d{13})")

        for div in divs:
            match = pattern.search(div.text)
            if match:
                barcode = match.group(1)
                barcode = re.sub(r"\D", "", barcode)  # Удаляем все символы, кроме цифр
                break
    except:
        pass

    try:
        manufacture = soup.find('span', attrs={'id': 'manufacture_30'}).text
        manufacture = re.sub(r'[\n/*,-/"+\\]', '_', manufacture).strip()
    except:
        manufacture = None
    try:
        manufacture_code = soup.find('a', class_="article_index_link").text
        manufacture_code = re.sub(r'[\n/*,-/"+\\]', '_', manufacture_code).strip()
    except:
        manufacture_code = None

    try:
        manufacture_name = soup.find('span', attrs={'id': 'name_30'}).text.replace("\n", "").strip()
    except:
        manufacture_name = None
    filenames = []
    img_dir = "c:\\intercars_img"
    filenames = []

    # Ограничиваем количество изображений до 4
    max_images = min(4, len(result))

    async with aiohttp.ClientSession() as session:
        tasks = []
        for idx, img in enumerate(result[:max_images]):
            filename = f"{manufacture_code}_{manufacture}_{idx + 1:02}.jpg"
            file_path = os.path.join(img_dir, filename)
            filenames.append(filename)

            if os.path.exists(file_path):
                continue

            tasks.append(download_image(session, img, file_path))

        if tasks:
            await asyncio.gather(*tasks)

    datas = [full_name, manufacture, manufacture_code, manufacture_name, barcode, filenames]
    writer.writerow(datas)


async def main():
    targetPattern = r"c:\intercars_html\*.html"
    files_html = glob.glob(targetPattern)

    async with aiohttp.ClientSession() as session, aiofiles.open("data.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=';')

        tasks = [process_file(session, item, writer) for item in files_html]
        await asyncio.gather(*tasks)



if __name__ == '__main__':
    asyncio.run(main())
