# parsing/html_parser.py
from bs4 import BeautifulSoup


class HTMLParser:
    @staticmethod
    def parse_ean(soup):
        ean_tag = soup.find("meta", itemprop="gtin")
        return ean_tag["content"] if ean_tag else None

    @staticmethod
    def parse_brand(soup):
        brand_tag = soup.find("meta", itemprop="brand")
        return brand_tag["content"] if brand_tag else None

    @staticmethod
    def parse_name(soup):
        name_tag = soup.find("meta", itemprop="name")
        return name_tag["content"] if name_tag else None

    # Similar methods for other fields...

    @staticmethod
    def parse_product_data(file_html):
        with open(file_html, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")

        return {
            "EAN": HTMLParser.parse_ean(soup),
            "Brand": HTMLParser.parse_brand(soup),
            "Name": HTMLParser.parse_name(soup),
            # Add other parsers here...
        }
