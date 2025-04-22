# /config/constants.py
from pathlib import Path

# Директории
BASE_DIR = Path.cwd()
GZ_DIR = BASE_DIR / "gz"
XML_DIR = BASE_DIR / "xml"
HTML_FILES_DIR = BASE_DIR / "html_files"
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"

# Файлы
XML_SITEMAP = DATA_DIR / "sitemap_index.xml"
CSV_URL_SITE_MAPS = DATA_DIR / "url_site_maps.csv"
OUTPUT_CSV_FILE = DATA_DIR / "output.csv"
CSV_ALL_URLS_PRODUCTS = DATA_DIR / "all_urls.csv"
CSV_ALL_EDRS_PRODUCTS = DATA_DIR / "all_edrs.csv"
CSV_FILE_SUCCESSFUL = DATA_DIR / "identifier_successful.csv"
XLSX_RESULT = DATA_DIR / "result.xlsx"
FILE_PROXY = CONFIG_DIR / "proxy.txt"

# Заголовки и куки
COOKIES = {
    "PHPSESSID": "ccf951766344e467fda99a2b57b0818b",
    "finance-indicators-mode": "percent",
}

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
}
