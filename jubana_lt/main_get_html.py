from pathlib import Path
import hashlib
import requests
from logger import logger
from bs4 import BeautifulSoup
current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)


cookies = {
    'PHPSESSID': 'dpi4t2rg8egdie161h24ubhs94',
    'user_id': '16bc70ad03a1ee7c6f7a6416ad792e8b',
    'hl': 'en',
    'cc_cookie': '%7B%22categories%22%3A%5B%22necessary%22%2C%22functionality%22%2C%22analytics%22%2C%22marketing%22%5D%2C%22revision%22%3A0%2C%22data%22%3Anull%2C%22consentTimestamp%22%3A%222025-04-07T14%3A49%3A25.656Z%22%2C%22consentId%22%3A%220df345d9-ed8d-4080-8940-82384cf29f49%22%2C%22services%22%3A%7B%22necessary%22%3A%5B%5D%2C%22functionality%22%3A%5B%5D%2C%22analytics%22%3A%5B%5D%2C%22marketing%22%3A%5B%5D%7D%2C%22lastConsentTimestamp%22%3A%222025-04-07T14%3A49%3A25.656Z%22%2C%22expirationTime%22%3A1759762165656%7D',
    '_ga': 'GA1.1.1924005572.1744037364',
    'session': 'Ym04U4MTqOO%2BN0czS%2B23SAk%2BD6EJU%2BaM9ju44AlML20moPgiFOEVfA%2Bs1kshuYl8nO10CFNM8AVfr%2B17X2gCy8veRN5E3d9cP3sDn%2BL%2F%2FGk2s6FBkB5c0SJ7UjHcXzR6Afj626U8B7CLVysjcU8%2Bi%2FFxd3oyZ9tkbEHnYqmwv3nF1z%2BiTy6wdl6niS%2FiNBUBCsUi55S5AFzGZgcZFOwgJS07QZbxNH3witUQL7DNTj5J%2FJq1w1ImJOoYWST1PVE%2FNZtKXFjfrfOkQWGftoiq4vEtKOhWUodx7ZRSvANm321BAjM6IkXOiiXgtW16AAjAVDtGuJWq1ZJupSXRwOp7W%2FPPJNsZVHiBfr1TQQBpu9g0S6sNlfoGlkkWW9eeKGy1SGfUD%2B0pmr5Du95gPRjdkMnEvIhDZ5PJ%2F8YBtZIHRgw%3D',
    '_ga_GW4HQBTRK8': 'GS1.1.1744037364.1.0.1744037370.55.0.0',
    '_fbp': 'fb.1.1744037370658.118763979501395736',
    '_gcl_au': '1.1.969105155.1744037371',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en;q=0.9,uk;q=0.8',
    'cache-control': 'no-cache',
    'dnt': '1',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://www.jubana.lt/en/starters/starters-12v',
    'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
}
def get_html_page(catefoty_name, url):

    
    catefoty_directory = html_directory / catefoty_name
    catefoty_directory.mkdir(parents=True, exist_ok=True)
    output_html_catefoty_file = catefoty_directory / f"page_{catefoty_name}.html"
    if output_html_catefoty_file.exists():
        logger.info(f"HTML file already exists: {output_html_catefoty_file}")
        return
    response = requests.get(url, cookies=cookies, headers=headers, timeout=30)

    # Проверка кода ответа
    if response.status_code == 200:

        # Сохранение HTML-страницы целиком
        with open(output_html_catefoty_file, "w", encoding="utf-8") as file:
            file.write(response.text)
        logger.info(f"Successfully saved {output_html_catefoty_file}")
    else:
        logger.error(f"Failed to get HTML. Status code: {response.status_code}")

def scrap_page(catefoty):
    """
    Находит все блоки товаров и извлекает ссылки на страницы продуктов.
    
    Args:
        html_content (str): HTML содержимое страницы
        
    Returns:
        list: Список URL-адресов продуктов
    """
    try:
        catefoty_directory = html_directory / catefoty
        catefoty_directory.mkdir(parents=True, exist_ok=True)
        output_html_catefoty_file = catefoty_directory / f"page_{catefoty}.html"
        with open(output_html_catefoty_file, "r", encoding="utf-8") as file:
            content = file.read()
        
        soup = BeautifulSoup(content, "lxml")
        product_links = []
        
        # Находим все блоки с информацией о товарах
        item_containers = soup.select('.item-info-container')
        
        for container in item_containers:
            # Находим ссылку внутри контейнера
            link = container.select_one('a.item_hover_wrap_link')
            
            if link and link.has_attr('href'):
                product_links.append(link['href'])
        
        return product_links
    
    except Exception as e:
        print(f"Ошибка при извлечении ссылок на продукты: {e}")
        return []

def get_html(catefoty_name, url):

    
    catefoty_directory = html_directory / catefoty_name
    catefoty_directory.mkdir(parents=True, exist_ok=True)
    output_html_catefoty_file = catefoty_directory / f"{hashlib.md5(url.encode()).hexdigest()}.html"
    if output_html_catefoty_file.exists():
        logger.info(f"HTML file already exists: {output_html_catefoty_file}")
        return
    response = requests.get(url, cookies=cookies, headers=headers, timeout=30)

    # Проверка кода ответа
    if response.status_code == 200:

        # Сохранение HTML-страницы целиком
        with open(output_html_catefoty_file, "w", encoding="utf-8") as file:
            file.write(response.text)
        logger.info(f"Successfully saved {output_html_catefoty_file}")
    else:
        logger.error(f"Failed to get HTML. Status code: {response.status_code}")
