from bs4 import BeautifulSoup
import csv


def parse_html_file(file_path):
    # Открытие и чтение файла
    with open(file_path, 'r', encoding='utf-8') as file:
        page_content = file.read()

    # Создание объекта BeautifulSoup
    heandler = ['test_name', 'term_text', 'data_sr_id', 'data_service_id', 'category', 'price']
    with open('output.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(heandler)  # Записываем заголовки только один раз
        soup = BeautifulSoup(page_content, "lxml")
        table_results = soup.find('div', attrs={'class': 'results results-analyzes'})

        for div in table_results.find_all('div', attrs={'class': 'result'}):
            test_name = div.find('a').get_text(strip=True)
            data_sr_id = div.find('div', attrs={'class': 'cell__value open-research-detail'}).get(
                'data-sr-id')
            data_service_id = div.find('div', attrs={'class': 'cell__value open-research-detail'}).get(
                'data-service-id')
            category = div.find('div', attrs={'class': 'cell__value open-research-detail'}).find('div',
                                                                                                 attrs={
                                                                                                     'class': 'cell__label'}).get_text(
                strip=True)
            term_div = div.find_all('div', attrs={'class': 'result__info'})
            if len(term_div) > 1 and term_div[1].div:
                term = term_div[1].div.find('div', attrs={'class': 'cell__value'})
                term_text = term.get_text(strip=True) if term else 'Unknown Term'
            else:
                term_text = None
            price_div = div.find('div', attrs={'class': 'discount-analyzes'})
            if price_div and price_div.find('span'):
                price = price_div.find('span').get_text(strip=True)
            else:
                price = None
            values = [test_name, term_text, data_sr_id, data_service_id, category, price]
            writer.writerow(values)



# Путь к файлу, который нужно проанализировать
file_path = 'page_content.html'
parse_html_file(file_path)
