from dateutil.relativedelta import relativedelta
from phonenumbers import NumberParseException
from mysql.connector import errorcode
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from threading import Lock
import mysql.connector
import phonenumbers
import threading
import requests
import datetime
import random
import json
import os
import re

# Параметры подключения к базе данных
config = {
    'user': '',
    'password': '',
    'host': '',
    'database': ''
}

# Регулярные выражения и функции для извлечения номеров
polish_phone_patterns = {
    "full": r"\b(48\d{9}|\d{9})\b",
    "split": r"(48\d{9})",
    "final": r"\b(\d{9})\b",
    "codes": [48]
}

# Файл для хранения ссылок
links_file = f'links_file.txt'
# Объект Lock для синхронизации потоков
lock = Lock()
# Константы для форматирования текста в консоли
RED = "\033[31m"
RESET = "\033[0m"

# Функция для записи данных в файл
def write_data(data, filename):
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(f"{data}\n")

# Функция для извлечения номеров телефонов из текста
def extract_phone_numbers(data):
    phone_numbers = set()
    invalid_numbers = []
    phone_pattern = re.compile(r'\d{3}\s\d{3}\s\d{3}|\(\d{3}\)\s\d{3}\-\d{3}|\b\d[\d\s\(\)\-]{6,}\b|\d{3}[^0-9a-zA-Z]*\d{3}[^0-9a-zA-Z]*\d{3}')
    for entry in data:
        if isinstance(entry, str):
            matches = phone_pattern.findall(entry)
            for match in matches:
                original_match = match
                match = re.sub(r'[^\d]', '', match)
                match = re.sub(r'^0+', '', match)
                try:
                    parsed_number = phonenumbers.parse(match, "PL")
                    if phonenumbers.is_valid_number(parsed_number):
                        national_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)
                        clean_number = ''.join(filter(str.isdigit, national_number))
                        phone_numbers.add(clean_number)
                    else:
                        invalid_numbers.append(original_match)
                except NumberParseException:
                    invalid_numbers.append(original_match)
    return phone_numbers, invalid_numbers

# Функция для получения HTML-кода страницы по URL
def get_url(url):
    counter_error = 0

    print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Получение страницы {url}.')

    # Генерация случайного User-Agent
    ua = UserAgent()

    # Загрузка списка прокси из файла
    proxies = [line.strip() for line in open('/home/parsing/1000 ip.txt', 'r', encoding='utf-8')]

    # Пока есть доступные прокси, пытаемся загрузить страницу
    while proxies:
        if len(proxies) > 0:
            proxy = random.choice(proxies)
        else:
            print("Список прокси пуст")
            return None

        proxies_dict = {
            'http': proxy,
            'https': proxy,
        }

        try:
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
                'User-Agent': ua.random,
            }

            # Отправка GET-запроса на сайт
            response = requests.get(
                url=url,
                timeout=60,
                headers=headers,
                proxies=proxies_dict,
            )

            # Если ответ успешный (200), возвращаем HTML-код
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup
            elif response.status_code == 403:
                # Если код ошибки 403, удаляем прокси и пробуем другой
                print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Код ошибки 403. Сайт нас подрезал.')
                proxies.remove(proxy)
                print(proxy)
                print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Осталось прокси {len(proxies)}')
                counter_error += 1
                if counter_error == 10:
                    print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Перезапуск, нас подрезали.')
                    return None
            else:
                return None
        except requests.exceptions.TooManyRedirects:
            print("Произошла ошибка: Exceeded 30 redirects. Пропуск.")
            return 'Редирект'
        except (requests.exceptions.ProxyError, requests.exceptions.Timeout):
            proxies.remove(proxy)
            print(proxy)
            print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Осталось прокси {len(proxies)}')
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            continue

    return None

# Функция для получения информации о странице и обработке найденных ссылок
def get_info(url, filename, links_counter_file, thread_id, lock):
    print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Обрабатывается категория {url} | (Поток -> {thread_id})')
    print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Получение следующей страницы | (Поток -> {thread_id})')

    with lock:
        soup = get_url(url=url)

    if soup == 'Редирект':
        return None

    if soup is None:
        return url
    
    next_page_link = None

    # Поиск ссылки на следующую страницу
    next_page_element = soup.find('a', class_='pagination__nextPage')
    if next_page_element and 'href' in next_page_element.attrs:
        next_page_link = next_page_element['href']
        print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Следующая страница - {next_page_link} | (Поток -> {thread_id})')
        
    links = set()

    # Извлечение всех ссылок на объявления
    for element in soup.find_all('a', class_='teaserLink'):
        if 'href' in element.attrs:
            links.add(element['href'])

    with lock:
        # Чтение существующих ссылок из файла, чтобы избежать дублирования
        if os.path.exists(links_file):
            with open(links_file, 'r', encoding='utf-8') as file:
                existing_links = set(file.read().splitlines())
            links.difference_update(existing_links)
            
    for link in links:
        print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - Обрабатывается объявление {link}')

        with lock:
            soup = get_url(link)

        if soup == 'Редирект':
            continue

        if soup is None:
            continue

        # Инициализация переменных для хранения данных объявления
        location = None
        time_posted = None
        mail_address = None
        phone_numbers = set()

        # Извлечение данных из HTML-кода объявления
        with lock:
            relative_box = soup.find('div', class_='offer__relativeBox')
            if relative_box:
                script_tag = relative_box.find('script')
                if script_tag:
                    script_content = script_tag.string
                    match = re.search(r'offerDetails:\s*({.*?})\s*,', script_content, re.DOTALL)
                    if match:
                        offer_details_str = match.group(1)
                        location_match = re.search(r"location:\s*'([^']+)'", offer_details_str)
                        if location_match:
                            location_soup = BeautifulSoup(location_match.group(1), 'html.parser')
                            location = ', '.join(filter(None, [region.strip() for region in location_soup.get_text().split(',')]))
                            location = location.replace(';', ',').replace('\n', '').replace('\r', '').replace('\t', '').strip()
                        phone_match = re.search(r"data-full-phone-number=\"([^\"]+)\"", offer_details_str)
                        if phone_match:
                            phone_numbers.add(phone_match.group(1).replace(';', ',').replace('\n', '').replace('\r', '').replace('\t', '').strip())

            if not location:
                container = soup.find('div', id='contact_container')
                if container:
                    address_div = container.find('div', class_='offerOwner__address')
                    if address_div:
                        location = address_div.get_text(strip=True)
                        location = location.replace(';', ',').replace('\n', '').replace('\r', '').replace('\t', '').strip()

            if not location:
                h2_element = soup.find('h2', class_='_5cxNyc undefined', attrs={'data-v-54164881': True})
                if h2_element:
                    location_parts = [span.get_text(strip=True) for span in h2_element.find_all('span')]
                    location = ' '.join(location_parts)

            if not location:
                location_span = soup.find('span', class_='offerLocation')
                if location_span:
                    location_parts = location_span.find_all('span', class_='offerLocation__region')
                    location = ' '.join(part.get_text(strip=True) for part in location_parts)

            phone_spans = soup.find_all('span', class_='phoneSmallButton')
            for span in phone_spans:
                a_tag = span.find('a', class_='phoneSmallButton__button')
                if a_tag and 'data-full-phone-number' in a_tag.attrs:
                    phone_numbers.add(a_tag['data-full-phone-number'].replace(';', ',').replace('\n', '').replace('\r', '').replace('\t', '').strip())

            script_tag = soup.find('script', type='application/ld+json')
            if script_tag:
                try:
                    json_data = json.loads(script_tag.string)
                    if 'seller' in json_data and 'telephone' in json_data['seller']:
                        phone_number = json_data['seller']['telephone']
                        phone_numbers.add(phone_number.replace(';', ',').replace('\n', '').replace('\r', '').replace('\t', '').strip())
                except json.JSONDecodeError as e:
                    print(f"Ошибка при парсинге JSON: {e}")
            else:
                print("Тег <script> с type='application/ld+json' не найден.")

            script_tag = soup.find('script', type='application/json', attrs={'data-ssr': 'true'})
            if script_tag:
                try:
                    json_data = json.loads(script_tag.string)
                except json.JSONDecodeError:
                    print("Не удалось декодировать JSON данные.")
                    json_data = []

            def extract_phone_indices(data, index_set):
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key == "phones" and isinstance(value, int):
                            index_set.add(value)
                        else:
                            extract_phone_indices(value, index_set)
                elif isinstance(data, list):
                    for item in data:
                        extract_phone_indices(item, index_set)

            def get_phone_numbers(data, indices):
                phone_numbers = []
                for index in indices:
                    if isinstance(data[index], list):
                        for sub_index in data[index]:
                            if isinstance(data[sub_index], str):
                                phone_numbers.append(data[sub_index])
                    elif isinstance(data[index], str):
                        phone_numbers.append(data[index])
                return phone_numbers

            phone_indices = set()
            extract_phone_indices(json_data, phone_indices)
            phone_numbers.update(get_phone_numbers(json_data, phone_indices))

            # Извлечение и форматирование даты добавления или обновления объявления
            date_dodania = None
            aktualizacja = None
            elements = soup.find_all('div', class_='vZJg9t')
            for element in elements:
                span = element.find('span', string='Data dodania') or element.find('span', string='Aktualizacja')
                if span:
                    date_div = element.find('div', {'data-cy': 'itemValue'})
                    if date_div:
                        date_text = date_div.get_text(strip=True)
                        match = re.match(r'(\d{2})\.(\d{2})\.(\d{4})', date_text)
                        if match:
                            day, month, year = match.groups()
                            date_obj = datetime.datetime(int(year), int(month), int(day))
                            formatted_date = date_obj.strftime('%Y-%m-%d')
                            if span.get_text(strip=True) == 'Data dodania':
                                date_dodania = formatted_date
                            elif span.get_text(strip=True) == 'Aktualizacja':
                                aktualizacja = formatted_date
            if aktualizacja and (not date_dodania or aktualizacja > date_dodania):
                time_posted = aktualizacja
            else:
                time_posted = date_dodania

            if not time_posted:
                # Функция для извлечения даты по текстовому описанию
                def extract_time(date_text):
                    current_time = datetime.datetime.now()

                    if date_text == 'dziś':
                        return current_time
                    elif date_text == 'wczoraj':
                        return current_time - datetime.timedelta(days=1)
                    elif date_text == 'przedwczoraj':
                        return current_time - datetime.timedelta(days=2)
                    elif 'tydzień temu' in date_text или 'ponad tydzień temu' в date_text:
                        return current_time - datetime.timedelta(days=7)
                    elif 'dwa tygodnie temu' в date_text или 'ponad dwa tygodnie temu' в date_text:
                        return current_time - datetime.timedelta(days=14)
                    elif 'miesiąc temu' в date_text или 'ponad miesiąc temu' в date_text:
                        return current_time - relativedelta(months=1)
                    elif 'pół roku temu' в date_text или 'ponad pół roku temu' в date_text:
                        return current_time - relativedelta(months=6)
                    else:
                        match = re.search(r'(\d+) dni temu', date_text)
                        if match:
                            days_ago = int(match.group(1))
                            return current_time - datetime.timedelta(days=days_ago)
                        return date_text

                li_tags = soup.find_all('li')

                for li in li_tags:
                    for element in li:
                        if element.name == 'span' and element.text.strip() == 'Zaktualizowane':
                            for sibling in li:
                                if sibling.name == 'div' and sibling.get('class') == ['parameters__value']:
                                    date_text = sibling.text.strip()
                                    time_posted = extract_time(date_text)
                                    break
                    if time_posted is not None:
                        break

                if time_posted is None:
                    for li in li_tags:
                        for element in li:
                            if element.name == 'span' и element.text.strip() == 'Dodane':
                                for sibling in li:
                                    if sibling.name == 'div' и sibling.get('class') == ['parameters__value']:
                                        date_text = sibling.text.strip()
                                        time_posted = extract_time(date_text)
                                        break
                        if time_posted is not None:
                            break

                if time_posted is not None:
                    if isinstance(time_posted, datetime.datetime):
                        time_posted = time_posted.strftime('%Y-%m-%d')

                print("Дата обновления или добавления:", time_posted)

            print(RED,f'{link}\nНомера - {phone_numbers}\nЛокация - {location}',RESET)

            # Форматирование данных для записи
            data = f'{None};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{link};{mail_address};{time_posted}'
            for phone_number in phone_numbers:
                data = f'{phone_number};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{link};{mail_address};{time_posted}'
                print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - {data} | (Поток -> {thread_id})')
                write_data(data=data, filename=filename)

            # Разбиваем строку на переменные
            _, location, timestamp, link, mail_address, time_posted = data.split(';')
            date_part, time_part = timestamp.split(' ')

            # Параметры для вставки в таблицу
            site_id = 6  # id_site для 'https://gratka.pl/'

            # Подключение к базе данных и запись данных
            try:
                cnx = mysql.connector.connect(**config)
                cursor = cnx.cursor(buffered=True)  # Используем buffered=True для извлечения всех результатов

                insert_announcement = (
                    "INSERT INTO ogloszenia (id_site, poczta, адрес, дата, время, link_do_ogloszenia, time_posted) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                )

                announcement_data = (site_id, mail_address, location, date_part, time_part, link, time_posted)

                cursor.execute(insert_announcement, announcement_data)

                cnx.commit()  # Убедитесь, что изменения зафиксированы, прежде чем получить id

                # Получение id_ogloszenia с помощью SELECT-запроса
                select_query = (
                    "SELECT id_ogloszenia FROM ogloszenia "
                    "WHERE id_site = %s AND poczta = %s И адрес = %s AND дата = %s И время = %s AND link_do_ogloszenia = %s И time_posted = %s"
                )
                cursor.execute(select_query, (site_id, mail_address, location, date_part, time_part, link, time_posted))
                
                # Извлечение результата и проверка наличия данных
                result = cursor.fetchone()
                if result:
                    id_ogloszenia = result[0]
                else:
                    print("Не удалось получить id_ogloszenia")
                    # Пропустить обработку, если id не найден
                    raise ValueError("Не удалось получить id_ogloszenia")

                # Заполнение таблицы numbers, если номера телефонов присутствуют
                if phone_numbers и id_ogloszenia:
                    phone_numbers_extracted, invalid_numbers = extract_phone_numbers(phone_numbers)
                    valid_numbers = [num for num in phone_numbers_extracted if re.match(polish_phone_patterns["final"], num)]
                    if valid_numbers:
                        clean_numbers = ', '.join(valid_numbers)
                    else:
                        clean_numbers = 'invalid'

                    insert_numbers = (
                        "INSERT INTO numbers (id_ogloszenia, raw, correct) "
                        "VALUES (%s, %s, %s)"
                    )
                    raw_numbers = ', '.join(phone_numbers)
                    numbers_data = (id_ogloszenia, raw_numbers, clean_numbers)
                    cursor.execute(insert_numbers, numbers_data)

                    cnx.commit()
                    print("Данные успешно добавлены в таблицы numbers и ogloszenia.")
                else:
                    print("Нет номеров телефонов для добавления в таблицу numbers.")

            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    print("Ошибка доступа: Неверное имя пользователя или пароль")
                elif err.errno == errorcode.ER_BAD_DB_ERROR:
                    print("Ошибка базы данных: База данных не существует")
                else:
                    print(err)
            finally:
                cursor.close()
                cnx.close()
                print("Соединение с базой данных закрыто.")

                # Увеличение счетчика обработанных ссылок
                links_count = 1

                if os.path.exists(links_counter_file):
                    with open(links_counter_file, 'r', encoding='utf-8') as f:
                        total_links_count = int(f.read().strip())
                        links_count += total_links_count

                with open(links_counter_file, 'w', encoding='utf-8') as f:
                    f.write(str(links_count))

                with open(links_file, 'a', encoding='utf-8') as file:
                    file.write(link + '\n')

    if next_page_link:
        return next_page_link
    else:
        return None

# Основная функция, которая запускает многопоточную обработку
def main_thread(url, thread_id, lock):
    page_file = f'page_{thread_id}.txt'
    filename = f'Польша - gratka_{thread_id}.csv'
    links_counter_file = f'links_counter_{thread_id}.txt'

    while True:
        next_page_link = get_info(url=url, filename=filename, links_counter_file=links_counter_file, thread_id=thread_id, lock=lock)

        if next_page_link:
            url = next_page_link
            with open(page_file, 'w', encoding='utf-8') as f:
                f.write(url)
            continue
        else:
            break

# Точка входа в программу, инициализирует потоки для обработки URL
def main():
    urls = open('category.txt', 'r', encoding='utf-8').read().splitlines()
    threads = []
    lock = Lock()

    # Запуск потоков для каждого URL
    for i, url in enumerate(urls):
        thread = threading.Thread(target=main_thread, args=(url, i, lock))
        threads.append(thread)
        thread.start()

    # Ожидание завершения всех потоков
    for thread in threads:
        thread.join()

if __name__ == '__main__':
    main()
