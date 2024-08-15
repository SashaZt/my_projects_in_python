import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import csv

xml_directory = Path("xml")
xml_directory.mkdir(exist_ok=True)

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


def download_and_parse_main_xml():

    main_url = "https://zorrov.com/image_sitemap.xml"
    # Скачиваем основной файл
    response = requests.get(main_url, headers=headers)

    if response.status_code == 200:
        # Парсим основной XML-файл
        root = ET.fromstring(response.content)

        # Обходим все элементы <loc>
        for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
            file_url = loc.text
            if file_url:
                # Извлекаем имя файла из URL и скачиваем его
                file_name = Path(file_url).name
                save_path = xml_directory / file_name
                download_xml(file_url, save_path)
    else:
        print(f"Ошибка при скачивании основного файла: {response.status_code}")


def download_xml(url: str, save_path: Path):
    response = requests.get(url)

    if response.status_code == 200:
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Файл успешно сохранен: {save_path}")
    else:
        print(f"Ошибка при скачивании файла {url}: {response.status_code}")


def parse_xml_files():
    output_csv = Path("urls.csv")
    all_loc_urls = []

    for xml_file in xml_directory.glob("*.xml"):
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for url in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
            loc = url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            if loc is not None:
                all_loc_urls.append(loc.text)

    # Сохраняем все URL в CSV-файл
    with open(output_csv, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["url"])
        for url in all_loc_urls:
            writer.writerow([url])


if __name__ == "__main__":
    download_and_parse_main_xml()
    parse_xml_files()
