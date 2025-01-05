import getpass
import glob
import json
import os
import sqlite3
import time
from datetime import datetime, timedelta

import gspread
import requests
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials

from config import spreadsheet_id, headers, dict_comany_edrpo

current_directory = os.getcwd()
temp_directory = 'temp'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
json_path = os.path.join(temp_path, 'json')
html_path = os.path.join(temp_path, 'html')


def get_google():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
    creds_file = os.path.join(current_directory, 'access.json')
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    return client, spreadsheet_id


#Создание временых папок"""


def creative_temp_folders():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, json_path, html_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)


#Получение всех тендеров"""

# def get_all_tenders():
#     params = {
#         'cpv[0]': '39160000-1',
#         'status[0]': 'active.enquiries',
#         'status[1]': 'active.tendering',
#         'filterType': 'tenders',
#     }
#
#     response = requests.post('https://prozorro.gov.ua/api/search/tenders', params=params,
#                              headers=headers)
#
#     json_data = response.json()
#     filename_all_tenders = os.path.join(json_path, 'all_tenders.json')
#     with open(filename_all_tenders, 'w', encoding='utf-8') as f:
#         json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл


#Парсинг всех тендеров"""

# def pars_all_tenders():
#     filename_all_tenders = os.path.join(json_path, 'all_tenders.json')
#     with open(filename_all_tenders, 'r', encoding="utf-8") as f:
#         data_json = json.load(f)
#

#Получение одного тендера"""


def get_tender(url_tender):
    id_url = url_tender.split('/')[-1]
    response = requests.get(url_tender, headers=headers)
    src = response.text
    filename_tender = os.path.join(html_path, f'tender_{id_url}.html')
    with open(filename_tender, "w", encoding='utf-8') as file:
        file.write(src)


#Парсинг одного тендера и извлечение json файла"""


def get_json_tender():
    filename_tender = os.path.join(html_path, 'tender_*.html')
    filenames = glob.glob(filename_tender)
    all_objects = []
    for filename in filenames:
        with open(filename, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        try:
            tender_id_full = soup.find('div', {'data-js': 'tender_sign_check'}).get('data-url')
        except:
            tender_id_full = soup.find('input', {'name': 'tenderId'}).get('value')
        tender_id = tender_id_full.split('/')[-1]
        # response = requests.get(tender_id, headers=headers)
        response = requests.get(f"https://public-api.prozorro.gov.ua/api/2.5/tenders/{tender_id}", headers=headers)
        json_data = response.json()
        filename_tender = os.path.join(json_path, f'tender_{tender_id}.json')
        with open(filename_tender, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
        time.sleep(10)


def parsing_tender(tenderID):
    filename_tender = os.path.join(html_path, f'tender_{tenderID}.html')
    with open(filename_tender, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    try:
        tender_id_full = soup.find('div', {'data-js': 'tender_sign_check'}).get('data-url')
    except:
        tender_id_full = soup.find('input', {'name': 'tenderId'}).get('value')
    tender_id = tender_id_full.split('/')[-1]

    return tender_id


"""Функции которые будут извлекать значения"""

"""Аукцион дата и время"""


def extract_auction_period_dates(json_data):
    # Получаем список лотов, по умолчанию используем пустой список, если 'lots' не существует
    lots = json_data.get('lots', [{}])

    # Пытаемся извлечь дату начала аукциона
    auctionPeriod_startDate = lots[0].get('auctionPeriod', {}).get('startDate')

    if auctionPeriod_startDate:
        # Преобразуем строку в объект datetime
        datetime_obj = datetime.fromisoformat(auctionPeriod_startDate)

        # Форматируем дату и время в требуемые строки
        date_auctionPeriod = datetime_obj.strftime("%d.%m.%Y")
        time_auctionPeriod = datetime_obj.strftime("%H:%M")
    else:
        # Если дата начала аукциона не указана, возвращаем None
        date_auctionPeriod = time_auctionPeriod = None

    return date_auctionPeriod, time_auctionPeriod


"""Кінцевий строк подання тендерних пропозицій"""

def extract_tenderPeriod(json_data):
    lots = json_data.get('lots', [{}])
    # Ваш изначальный код для получения значения
    tenderPeriod_endDate = json_data.get('tenderPeriod', {}).get('endDate')

    # Инициализируем возвращаемые переменные
    date_tenderPeriod = None
    time_tenderPeriod = None

    try:
        # Проверяем, существует ли дата закрытия тендера
        if tenderPeriod_endDate:
            # Преобразуем строку в объект datetime
            datetime_obj = datetime.fromisoformat(tenderPeriod_endDate)

            # Проверяем, равно ли время "00:00"
            if datetime_obj.hour == 0 and datetime_obj.minute == 0:
                # Вычитаем один день и устанавливаем время на "23:59"
                date_tenderPeriod = (datetime_obj - timedelta(days=1)).strftime("%d.%m.%Y")
                time_tenderPeriod = "23:59"

            else:
                # Если время не "00:00", используем исходные дату и время
                date_tenderPeriod = datetime_obj.strftime("%d.%m.%Y")
                time_tenderPeriod = datetime_obj.strftime("%H:%M")

    except Exception as e:
        # Выводим ошибку, если преобразование даты не удалось
        print(f"Ошибка при обработке даты: {e}")
    # Возвращаем обработанные дату и время
    return date_tenderPeriod, time_tenderPeriod


"""Звернення за роз’ясненням"""


def enquiryPeriod_endDate(json_data):
    enquiryPeriod_endDate = json_data.get('enquiryPeriod', {}).get('endDate')
    if enquiryPeriod_endDate:
        datetime_obj_enquiryPeriod_endDate = datetime.fromisoformat(enquiryPeriod_endDate)

        date_enquiryPeriod_endDate = datetime_obj_enquiryPeriod_endDate - timedelta(days=1)
        date_enquiryPeriod_endDate = date_enquiryPeriod_endDate.strftime("%d.%m.%Y")

        datetime_obj_minus_one_minute = datetime_obj_enquiryPeriod_endDate - timedelta(minutes=1)
        time_enquiryPeriod_endDate = datetime_obj_minus_one_minute.strftime("%H:%M")
    else:
        date_enquiryPeriod_endDate = time_enquiryPeriod_endDate = None

    return date_enquiryPeriod_endDate, time_enquiryPeriod_endDate


"""Розмір надання забезпечення пропозицій учасників"""


def guarantee_bank(json_data):
    if json_data.get('guarantee', {}):
        guarantee_amount = json_data.get('guarantee', {}).get('amount', None)
    else:
        guarantee_amount = None
    if len(json_data.get('criteria', [])) > 10:
        criteria = json_data.get('criteria')[10]  # Безопасно получаем элемент с индексом 10
        requirementGroups = criteria.get('requirementGroups', [{}])[0]  # Безопасно получаем первый элемент списка
        requirements = requirementGroups.get('requirements', [{}])[0]  # Безопасно получаем первый элемент
        bank_garantiy = requirements.get('description', None)  # И, наконец, получаем 'description'

        # Проверяем, содержит ли bank_garantiy нужный текст, только если bank_garantiy не None
        if bank_garantiy:  # Проверяет, не пустая ли строка и не None ли она
            bank_garantiy = 'Да'
        else:
            bank_garantiy = None
    else:
        bank_garantiy = None  # Если элементов в списке 'criteria' меньше 11, возвращаем None
    return guarantee_amount, bank_garantiy


"""Парсинг одного тендера json"""


def pars_tender():
    # dick_tender = get_all_tender_records_as_dicts()

    filename_tender = os.path.join(json_path, 'tender*.json')
    filenames = glob.glob(filename_tender)
    for filename in filenames:
        with open(filename, 'r', encoding="utf-8") as f:
            data_json = json.load(f)
        json_data = data_json.get('data', {})
        status_tender = json_data.get('status', None)
        tenderID = json_data.get('tenderID')
        tender_id = parsing_tender(tenderID)
        award_status = None
        bids_amount = None
        tender_verification = None
        url_tender = f"https://prozorro.gov.ua/tender/{tenderID}"
        customer = json_data.get('procuringEntity', {}).get('name', None)
        budget = json_data.get('value', [{}]).get('amount', None)

        """Жалоба"""
        complaint = None  # Устанавливаем complaint в None по умолчанию

        # Получаем списки жалоб и вопросов
        complaints_all = json_data.get('complaints', None)
        questions_all = json_data.get('questions', None)

        # Проверяем наличие и непустоту блоков complaints и/или questions
        if complaints_all or questions_all:
            complaint = "Увага!!!"
        # complaint = None  # Устанавливаем complaint в None по умолчанию
        # try:
        #     if complaint is None:
        #         complaints_all = json_data.get('complaints',
        #                                        None)  # Используем .get() для безопасного получения данных
        #         if complaints_all:  # Если есть жалобы для проверки
        #             for complaint_data in complaints_all:
        #                 if complaint_data.get('resolutionType') == 'resolved':  # Проверяем, решена ли жалоба
        #                     break  # Выходим из цикла, так как нашли решенную жалобу
        #             else:
        #                 # Если цикл завершился без break, значит не нашли решенных жалоб
        #                 complaint = "Увага!!!"
        #     questions_all = json_data.get('questions', None)  # Получаем список вопросов
        #     if questions_all is not None:  # Проверяем, что список вопросов существует
        #         for question in questions_all:  # Проходим по каждому вопросу
        #             if 'answer' not in question or not question[
        #                 'answer'].strip():
        #                 complaint = "Увага!!!"
        #                 break
        #
        # except Exception as e:
        #     print(f"Ошибка при обработке вопросов: {e}")

        """Аукцион дата и время"""
        date_auctionPeriod, time_auctionPeriod = extract_auction_period_dates(json_data)
        """Кінцевий строк подання тендерних пропозицій"""
        date_tenderPeriod, time_tenderPeriod = extract_tenderPeriod(json_data)
        """Звернення за роз’ясненням"""
        date_enquiryPeriod_endDate, time_enquiryPeriod_endDate = enquiryPeriod_endDate(json_data)
        """Розмір надання забезпечення пропозицій учасників"""
        guarantee_amount, bank_garantiy = guarantee_bank(json_data)

        """Победитель ЕДРПО"""
        # Инициализация переменных
        award_name_customer = None
        award_value_customer = None
        # edrpo_customer = None
        time_pending = None
        date_pending = None

        # Проверяем наличие и не пустоту списка 'awards'
        if json_data.get('awards'):
            first_award = json_data.get('awards')[0]  # Берем первый элемент из списка 'awards'
            dara_pending = first_award['date']
            datetime_obj_pending = datetime.fromisoformat(dara_pending)
            """Дата и время победившей ставки"""
            date_pending = datetime_obj_pending.strftime("%d.%m.%Y")
            time_pending = datetime_obj_pending.strftime("%H:%M")
            award_status = first_award.get('status', None)

            # Проверяем наличие и не пустоту списка 'suppliers'
            if first_award.get('suppliers'):
                first_supplier = first_award.get('suppliers')[0]  # Берем первый элемент из списка 'suppliers'

                # Извлекаем имя и EDRPOU код
                award_name_customer = first_supplier.get('name', None)  # Получаем имя
                identifier = first_supplier.get('identifier')  # Получаем identifier
                if identifier:  # Проверяем, что identifier существует
                    edrpo_customer = identifier.get('id', None)  # Извлекаем 'id'
                    if edrpo_customer in dict_comany_edrpo.values():
                        if award_status == 'pending':
                            award_status = None
                        if award_status == 'active':
                            award_status = 'Победа'
                        if award_status == 'unsuccessful':
                            award_status = None
                    else:
                        award_status = None
            # Для стоимости предложения победителя
            award_value = first_award.get('value')  # Получаем словарь 'value'
            if award_value:  # Проверяем, что словарь 'value' существует
                award_value_customer = award_value.get('amount', None)  # Получаем стоимость

        """Період уточнень"""
        if status_tender == 'active.enquiries':
            status_tender = 'Період уточнень'
            tender_verification = "0"

        """Подання пропозицій"""
        if status_tender == 'active.tendering':
            status_tender = 'Подання пропозицій'
            tender_verification = "0"

        """"Пропозиції розглянуті"""
        if status_tender == 'active.awarded':
            status_tender = 'Пропозиції розглянуті'
            tender_verification = "0"

        """Прекваліфікація (період оскарження)"""
        if status_tender == 'active.pre-qualification.stand-still':
            status_tender = 'Прекваліфікація (період оскарження)'
            tender_verification = "0"

        """Аукціон"""
        if status_tender == 'active.auction':
            status_tender = 'Аукціон'
            tender_verification = '0'

        """Кваліфікація переможця"""
        if status_tender == 'active.qualification':
            status_tender = 'Кваліфікація переможця'
            tender_verification = "0"

        """Пока поставлю для всех award_value_customer = None"""
        # award_name_customer = None

        """Завершена"""
        if status_tender == 'complete':
            status_tender = 'Завершена'
            tender_verification = "1"
            """Остаточна пропозиція"""
            # Получаем список bids из json_data
            bids = json_data.get('bids', [])
            # Проходим по каждому bid в списке
            for bid_index in range(len(bids)):
                # Получаем текущий bid по индексу
                current_bid = bids[bid_index]

                # Проверяем, есть ли 'tenderers' и это список
                tenderers = current_bid.get('tenderers', [])

                # Теперь итерируем по каждому tenderer
                for tenderer in tenderers:
                    # Извлекаем EDRPOU код tenderer
                    edrpou = tenderer.get('identifier', {}).get('id', None)

                    # Проверяем, есть ли edrpou в вашем словаре dict_comany_edrpo
                    if edrpou and edrpou in dict_comany_edrpo.values():
                        # print(f'+ Найден EDRPOU код: {edrpou}')

                        # После нахождения EDRPOU, получаем значение amount из lotValues
                        if 'lotValues' in current_bid:
                            for lotValue in current_bid['lotValues']:
                                bids_amount = lotValue.get('value', {}).get('amount', None)

                                if bids_amount is not None:
                                    continue
                                    # print(f'Сумма ставки: {bids_amount}')
                                else:
                                    continue
                                    # print('Сумма ставки не указана')
                        else:
                            continue
                            # print('Информация о lotValues отсутствует в данном bid')

                    else:
                        continue

        # Данные для вставки
        tender_data = {
            'tender_id': tender_id,
            'url_tender': url_tender,
            'customer': customer,
            'status_tender': status_tender,
            'complaint': complaint,
            'budget': budget,
            'date_auction': date_auctionPeriod,
            'time_auction': time_auctionPeriod,
            'bids_amount': bids_amount,
            'date_enquiryPeriod': date_enquiryPeriod_endDate,
            'time_enquiryPeriod': time_enquiryPeriod_endDate,
            'date_auctionPeriod_auctionPeriod': date_tenderPeriod,
            'time_auctionPeriod_auctionPeriod': time_tenderPeriod,
            'award_name_customer': award_name_customer,
            'award_value_customer': award_value_customer,
            'date_pending': date_pending,
            'time_pending': time_pending,
            'award_status': award_status,
            'guarantee_amount': guarantee_amount,
            'bank_garantiy': bank_garantiy,
            'tender_verification': tender_verification

        }
        filename_db = os.path.join(current_directory, 'prozorro.db')
        conn = sqlite3.connect(filename_db)
        c = conn.cursor()
        conn.execute('PRAGMA journal_mode=WAL;')
        # Проверяем, существует ли уже запись с таким tender_id
        c.execute("SELECT 1 FROM tender WHERE tender_id = ?", (tender_id,))
        exists = c.fetchone()

        if not exists:
            # Если записи не существует, выполняем вставку
            sql = '''INSERT INTO tender (
                        tender_id, url_tender, customer, status_tender,complaint,budget, date_auction, time_auction,bids_amount, date_enquiryPeriod,
                        time_enquiryPeriod, date_auctionPeriod_auctionPeriod, time_auctionPeriod_auctionPeriod,
                        award_name_customer, award_value_customer, date_pending, time_pending, award_status, guarantee_amount,
                        bank_garantiy,tender_verification
                     ) VALUES (
                        :tender_id, :url_tender, :customer, :status_tender, :complaint, :budget, :date_auction, :time_auction, :bids_amount, :date_enquiryPeriod,
                        :time_enquiryPeriod, :date_auctionPeriod_auctionPeriod, :time_auctionPeriod_auctionPeriod,
                        :award_name_customer, :award_value_customer, :date_pending, :time_pending, :award_status, :guarantee_amount,
                        :bank_garantiy, :tender_verification
                     )'''
            c.execute(sql, tender_data)
            conn.commit()
        else:
            print(f"Запись с tender_id {tender_id} уже существует. Пропускаем...")

        conn.close()
    """Открыть после завершения"""
    files_json = glob.glob(os.path.join(json_path, '*'))
    files_html = glob.glob(os.path.join(html_path, '*'))
    # Объединяем списки файлов
    all_files = files_json + files_html
    for f in all_files:
        if os.path.isfile(f):
            os.remove(f)


"""Обновление БД"""


def update_tenders_from_json():
    # # Получение списка текущих тендеров из базы данных
    dick_tender = get_all_tender_records_as_dicts()

    for d in dick_tender:
        tender_verification_bd = d['tender_verification']
        if tender_verification_bd != '1':
            url_ten = d['tender_id']
            filename_tender = os.path.join(json_path, f'tender_{url_ten}.json')
            if not os.path.exists(filename_tender):
                print(f'Качаем тендер {url_ten}')

                response = requests.get(f"https://public-api.prozorro.gov.ua/api/2.5/tenders/{url_ten}",
                                        headers=headers)
                try:
                    json_data = response.json()
                except:
                    print(f'Пропустили тендер {url_ten}')
                    continue

                with open(filename_tender, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
                time.sleep(10)
        else:
            print(f'Тендер {d["tender_id"]} завершен')

    # Словарь для перевода статусов из json в читаемый вид
    dict_status_tenders = {
        'active.auction': 'Аукціон',
        'complete': 'Завершена',
        'active.qualification': 'Кваліфікація переможця',
        'active.tendering': 'Подання пропозицій',
        'active.awarded': 'Пропозиції розглянуті',
        'active.enquiries': 'Період уточнень',
        'active.pre-qualification.stand-still': 'Прекваліфікація (період оскарження)'
    }

    filenames = glob.glob(os.path.join(json_path, 'tender*.json'))
    filename_db = os.path.join(current_directory, 'prozorro.db')
    with sqlite3.connect(filename_db) as conn:
        conn.execute('PRAGMA journal_mode=WAL;')
        c = conn.cursor()
        for filename in filenames:
            with open(filename, 'r', encoding="utf-8") as f:
                data_json = json.load(f)
                json_data = data_json.get('data', {})
                status_tender = json_data.get('status', None)
                tenderID = json_data.get('tenderID')
                url_tender = f"https://prozorro.gov.ua/tender/{tenderID}"
                get_tender(url_tender)
                tender_id = parsing_tender(tenderID)
                award_status = None
                bids_amount = None
                tender_verification = None

                customer = json_data.get('procuringEntity', {}).get('name', None)
                budget = json_data.get('value', [{}]).get('amount', None)

                """Жалоба"""
                complaint = None  # Устанавливаем complaint в None по умолчанию

                # Получаем списки жалоб и вопросов
                complaints_all = json_data.get('complaints', None)
                questions_all = json_data.get('questions', None)

                # Проверяем наличие и непустоту блоков complaints и/или questions
                if complaints_all or questions_all:
                    complaint = "Увага!!!"
                # """Жалоба"""
                # complaint = None  # Устанавливаем complaint в None по умолчанию
                # try:
                #     if complaint is None:
                #         complaints_all = json_data.get('complaints',
                #                                        None)  # Используем .get() для безопасного получения данных
                #         if complaints_all:  # Если есть жалобы для проверки
                #             for complaint_data in complaints_all:
                #                 if complaint_data.get('resolutionType') == 'resolved':  # Проверяем, решена ли жалоба
                #                     break  # Выходим из цикла, так как нашли решенную жалобу
                #             else:
                #                 # Если цикл завершился без break, значит не нашли решенных жалоб
                #                 complaint = "Увага!!!"
                #     questions_all = json_data.get('questions', None)  # Получаем список вопросов
                #     if questions_all is not None:  # Проверяем, что список вопросов существует
                #         for question in questions_all:  # Проходим по каждому вопросу
                #             if 'answer' not in question or not question[
                #                 'answer'].strip():
                #                 complaint = "Увага!!!"
                #                 break
                #
                # except Exception as e:
                #     print(f"Ошибка при обработке вопросов: {e}")

                """Аукцион дата и время"""
                date_auctionPeriod, time_auctionPeriod = extract_auction_period_dates(json_data)
                """Кінцевий строк подання тендерних пропозицій"""
                date_tenderPeriod, time_tenderPeriod = extract_tenderPeriod(json_data)
                """Звернення за роз’ясненням"""
                date_enquiryPeriod_endDate, time_enquiryPeriod_endDate = enquiryPeriod_endDate(json_data)
                """Розмір надання забезпечення пропозицій учасників"""
                guarantee_amount, bank_garantiy = guarantee_bank(json_data)

                """Победитель ЕДРПО"""
                # Инициализация переменных
                award_name_customer = None
                award_value_customer = None
                # edrpo_customer = None
                time_pending = None
                date_pending = None
                # if json_data.get('awards'):
                #     first_award = json_data['awards'][0]
                #     # Прямо здесь извлекаем дату и статус
                #     dara_pending = first_award.get('date')
                #     award_status = first_award.get('status')
                #
                #     # Обрабатываем 'suppliers', если он существует и не пуст
                #     if first_award.get('suppliers'):
                #         first_supplier = first_award['suppliers'][0]
                #         award_name_customer = first_supplier.get('name')
                #         identifier = first_supplier.get('identifier')
                #         if identifier:
                #             edrpo_customer = identifier.get('id')
                #             # Проверяем, соответствует ли edrpo_customer значению в dict_comany_edrpo
                #             if edrpo_customer in dict_comany_edrpo.values():
                #                 if award_status == 'pending':
                #                     award_status_resolved = None
                #                 elif award_status == 'active':
                #                     award_status_resolved = 'Победа'
                #                 elif award_status == 'unsuccessful':
                #                     award_status_resolved = None
                #
                #                 # Если статус 'Победа', обрабатываем 'value'
                #                 if award_status_resolved == 'Победа' and first_award.get('value'):
                #                     award_value_customer = first_award['value'].get('amount')
                #             else:
                #                 # Если edrpo_customer не находится в dict_comany_edrpo, обнуляем статус
                #                 award_status_resolved = None
                #
                #     # Обработка даты и времени только если дата существует
                #     if dara_pending:
                #         datetime_obj_pending = datetime.fromisoformat(dara_pending)
                #         date_pending = datetime_obj_pending.strftime("%d.%m.%Y")
                #         time_pending = datetime_obj_pending.strftime("%H:%M")
                # else:
                #     # Если 'awards' отсутствует, все переменные остаются None
                #     date_pending = time_pending = None

                """Рабочий код"""
                # Проверяем наличие и не пустоту списка 'awards'
                if json_data.get('awards'):
                    first_award = json_data.get('awards')[0]  # Берем первый элемент из списка 'awards'
                    dara_pending = first_award['date']
                    datetime_obj_pending = datetime.fromisoformat(dara_pending)
                    """Дата и время победившей ставки"""
                    date_pending = datetime_obj_pending.strftime("%d.%m.%Y")
                    time_pending = datetime_obj_pending.strftime("%H:%M")
                    award_status = first_award.get('status', None)

                    # Проверяем наличие и не пустоту списка 'suppliers'
                    if first_award.get('suppliers'):
                        first_supplier = first_award.get('suppliers')[0]  # Берем первый элемент из списка 'suppliers'

                        # Извлекаем имя и EDRPOU код
                        award_name_customer = first_supplier.get('name', None)  # Получаем имя
                        identifier = first_supplier.get('identifier')  # Получаем identifier
                        if identifier:  # Проверяем, что identifier существует
                            edrpo_customer = identifier.get('id', None)  # Извлекаем 'id'
                            if edrpo_customer in dict_comany_edrpo.values():
                                if award_status == 'pending':
                                    award_status = None
                                if award_status == 'active':
                                    award_status = 'Победа'
                                if award_status == 'unsuccessful':
                                    award_status = None
                            else:
                                award_status = None
                    # Для стоимости предложения победителя
                    award_value = first_award.get('value')  # Получаем словарь 'value'
                    if award_value:  # Проверяем, что словарь 'value' существует
                        award_value_customer = award_value.get('amount', None)  # Получаем стоимость
                if award_status == 'Победа':
                    award_value_customer = award_value.get('amount', None)  # Получаем стоимость
                else:
                    award_value_customer = None

                """Період уточнень"""
                if status_tender == 'active.enquiries':
                    status_tender = 'Період уточнень'
                    tender_verification = "0"

                """Подання пропозицій"""
                if status_tender == 'active.tendering':
                    status_tender = 'Подання пропозицій'
                    tender_verification = "0"

                """"Пропозиції розглянуті"""
                if status_tender == 'active.awarded':
                    status_tender = 'Пропозиції розглянуті'
                    tender_verification = "0"

                """Прекваліфікація (період оскарження)"""
                if status_tender == 'active.pre-qualification.stand-still':
                    status_tender = 'Прекваліфікація (період оскарження)'
                    tender_verification = "0"

                """Аукціон"""
                if status_tender == 'active.auction':
                    status_tender = 'Аукціон'
                    tender_verification = '0'

                """Кваліфікація переможця"""
                if status_tender == 'active.qualification':
                    status_tender = 'Кваліфікація переможця'
                    tender_verification = "0"

                """Пока поставлю для всех award_value_customer = None"""
                # award_name_customer = None

                """Завершена"""
                if status_tender == 'complete':
                    status_tender = 'Завершена'
                    tender_verification = "1"
                    """Остаточна пропозиція"""
                    # Получаем список bids из json_data
                    bids = json_data.get('bids', [])
                    # Проходим по каждому bid в списке
                    for bid_index in range(len(bids)):
                        # Получаем текущий bid по индексу
                        current_bid = bids[bid_index]

                        # Проверяем, есть ли 'tenderers' и это список
                        tenderers = current_bid.get('tenderers', [])

                        # Теперь итерируем по каждому tenderer
                        for tenderer in tenderers:
                            # Извлекаем EDRPOU код tenderer
                            edrpou = tenderer.get('identifier', {}).get('id', None)

                            # Проверяем, есть ли edrpou в вашем словаре dict_comany_edrpo
                            if edrpou and edrpou in dict_comany_edrpo.values():
                                # print(f'+ Найден EDRPOU код: {edrpou}')

                                # После нахождения EDRPOU, получаем значение amount из lotValues
                                if 'lotValues' in current_bid:
                                    for lotValue in current_bid['lotValues']:
                                        bids_amount = lotValue.get('value', {}).get('amount', None)

                                        if bids_amount is not None:
                                            continue
                                            # print(f'Сумма ставки: {bids_amount}')
                                        else:
                                            continue
                                            # print('Сумма ставки не указана')
                                else:
                                    continue
                                    # print('Информация о lotValues отсутствует в данном bid')

                            else:
                                continue
                # Данные для вставки
                tender_data = {
                    'tender_id': tender_id,
                    'url_tender': url_tender,
                    'customer': customer,
                    'status_tender': status_tender,
                    'complaint': complaint,
                    'budget': budget,
                    'date_auction': date_auctionPeriod,
                    'time_auction': time_auctionPeriod,
                    'bids_amount': bids_amount,
                    'date_enquiryPeriod': date_enquiryPeriod_endDate,
                    'time_enquiryPeriod': time_enquiryPeriod_endDate,
                    'date_auctionPeriod_auctionPeriod': date_tenderPeriod,
                    'time_auctionPeriod_auctionPeriod': time_tenderPeriod,
                    'award_name_customer': award_name_customer,
                    'award_value_customer': award_value_customer,
                    'date_pending': date_pending,
                    'time_pending': time_pending,
                    'award_status': award_status,
                    'guarantee_amount': guarantee_amount,
                    'bank_garantiy': bank_garantiy,
                    'tender_verification': tender_verification

                }

                # Проверяем, существует ли уже запись с таким tender_id
                c.execute("SELECT COUNT(*) FROM tender WHERE tender_id = ?", (tender_data['tender_id'],))
                exists = c.fetchone()[0] > 0
                if exists:
                    # Если запись существует, обновляем ее
                    sql_update = '''
                            UPDATE tender SET 
                                url_tender = :url_tender, 
                                customer = :customer,
                                status_tender = :status_tender,
                                complaint = :complaint,
                                budget = :budget,
                                date_auction = :date_auction,
                                time_auction = :time_auction,
                                bids_amount = :bids_amount,
                                date_enquiryPeriod = :date_enquiryPeriod,
                                time_enquiryPeriod = :time_enquiryPeriod,
                                date_auctionPeriod_auctionPeriod = :date_auctionPeriod_auctionPeriod,
                                time_auctionPeriod_auctionPeriod = :time_auctionPeriod_auctionPeriod,
                                award_name_customer = :award_name_customer,
                                award_value_customer = :award_value_customer,
                                date_pending = :date_pending,
                                time_pending = :time_pending,
                                award_status = :award_status,
                                guarantee_amount = :guarantee_amount,
                                bank_garantiy = :bank_garantiy,
                                tender_verification = :tender_verification
                            WHERE tender_id = :tender_id
                            '''
                    c.execute(sql_update, tender_data)
                else:
                    # Если запись не существует, вставляем новую
                    sql_insert = '''
                            INSERT INTO tender (
                                tender_id, url_tender, customer, status_tender, complaint, budget, 
                                date_auction, time_auction, bids_amount, date_enquiryPeriod, time_enquiryPeriod,
                                date_auctionPeriod_auctionPeriod, time_auctionPeriod_auctionPeriod, award_name_customer,
                                award_value_customer, date_pending, time_pending, award_status, guarantee_amount,
                                bank_garantiy, tender_verification
                            ) VALUES (
                                :tender_id, :url_tender, :customer, :status_tender, :complaint, :budget, 
                                :date_auction, :time_auction, :bids_amount, :date_enquiryPeriod, :time_enquiryPeriod, 
                                :date_tenderPeriod, :time_tenderPeriod, :award_name_customer, 
                                :award_value_customer, :date_pending, :time_pending, :award_status, :guarantee_amount, 
                                :bank_garantiy, :tender_verification
                            )
                            '''
                    c.execute(sql_insert, tender_data)

                    # Сохраняем изменения
                conn.commit()
    """Открыть после завершения"""

    files_json = glob.glob(os.path.join(json_path, '*'))
    files_html = glob.glob(os.path.join(html_path, '*'))
    # Объединяем списки файлов
    all_files = files_json + files_html
    for f in all_files:
        if os.path.isfile(f):
            os.remove(f)


#


"""Выгружает данные с БД"""


def get_url_from_sql():
    filename_db = os.path.join(current_directory, 'prozorro.db')
    conn = sqlite3.connect(filename_db)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT url_tender WHERE tender_id = :tender_id")
    records = c.fetchall()
    conn.close()
    return [dict(record) for record in records]


def get_all_tender_records_as_dicts():
    filename_db = os.path.join(current_directory, 'prozorro.db')
    conn = sqlite3.connect(filename_db)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT tender_id, customer, status_tender,tender_verification FROM tender")
    records = c.fetchall()
    conn.close()
    return [dict(record) for record in records]


"""Очистить данные"""


def clear_to_sheet():
    client, spreadsheet_id = get_google()
    sheet = client.open_by_key(spreadsheet_id).worksheet('Бюджетные')
    filename_db = os.path.join(current_directory, 'prozorro.db')
    conn = sqlite3.connect(filename_db)
    c = conn.cursor()

    # Выполняем SQL-запрос для выбора данных
    c.execute(
        '''SELECT tender_id, url_tender, customer,
        status_tender,complaint, date_auction, time_auction,
         bids_amount, date_enquiryPeriod, time_enquiryPeriod,
         date_auctionPeriod_auctionPeriod,
         time_auctionPeriod_auctionPeriod,
         award_name_customer, award_value_customer,
         date_pending, time_pending, award_status,
         guarantee_amount, bank_garantiy FROM tender''')

    # Получаем все строки
    rows_clear = c.fetchall()
    values = []
    """Очищаем поля"""
    for row in range(32):
        new_row = [None, None, '', '', '', '', None, None, '', None, None, None, None, None, None, '', '', '', '', '',
                   '', '', '', None, None, None, None, '', None, None, None, None]
        values.append(new_row)
    sheet.update(values, 'A3', value_input_option='USER_ENTERED')
    print('Даннные очистили')
    time.sleep(5)


"""запись данные"""


def write_to_sheet():
    client, spreadsheet_id = get_google()
    sheet = client.open_by_key(spreadsheet_id).worksheet('Бюджетные')
    filename_db = os.path.join(current_directory, 'prozorro.db')
    conn = sqlite3.connect(filename_db)
    c = conn.cursor()
    conn.execute('PRAGMA journal_mode=WAL;')

    # Выполняем SQL-запрос для выбора данных
    c.execute(
        '''SELECT tender_id, url_tender, customer,status_tender,complaint,budget,guarantee_amount,bank_garantiy,
        date_enquiryPeriod,time_enquiryPeriod,date_auctionPeriod_auctionPeriod,time_auctionPeriod_auctionPeriod,
         date_auction, time_auction,award_status, award_value_customer
         FROM tender''')
    """         award_name_customer, award_value_customer,
             date_pending, time_pending, award_status"""
    values = []
    rows = c.fetchall()
    for row in rows:
        # Создаем список из 32 элементов, заполненных None
        new_row = [None] * 32

        new_row[2] = row[1]  # url_tender
        new_row[3] = row[2]  # customer
        new_row[4] = row[3]  # status_tender
        new_row[5] = row[4]  # complaint
        new_row[8] = row[5].replace('.', ',')  # budget
        new_row[15] = row[6].replace('.', ',') if row[6] is not None else None  # guarantee_amount
        new_row[16] = row[7]  # bank_garantiy
        new_row[17] = row[8]  # date_enquiryPeriod
        new_row[18] = row[9]  # time_enquiryPeriod
        new_row[19] = row[10]  # date_auctionPeriod_auctionPeriod
        new_row[20] = row[11]  # time_auctionPeriod_auctionPeriod
        new_row[21] = row[12]  # date_auction
        new_row[22] = row[13]  # time_auction
        new_row[23] = row[14]  # award_status
        new_row[27] = row[15].replace('.', ',') if row[15] is not None else None  # award_value_customer

        # new_row = [None, None, '', '', '', None, None, '', None, None, None, None, None, None, '', '', '', '', '', '',
        #            '', '', '', None, None, None, '', None, None, None, None]
        # new_row = [None, None, row[1], row[2], row[3], None, None, row[4], None, None,
        #            row[7], '', '', '', row[17], row[18], row[8], row[9], row[10], row[11],
        #            row[5], row[6], row[16], '', '', '', row[13]]
        # new_row = [None, None, row[1], row[2], row[3], None, None, row[4], None, None, None, None, None, None, row[7], '', '', '', '', '', '',
        #            '', '', None, None, None, '', None, None, None, None]
        values.append(new_row)
    # Обновляем данные в Google Sheets, начиная с ячейки A15
    sheet.update(values, 'A3', value_input_option='USER_ENTERED')
    print('Даннные записали')


def clean_sql_table():
    filename_db = os.path.join(current_directory, 'prozorro.db')
    conn = sqlite3.connect(filename_db)
    c = conn.cursor()

    # Выполнение запроса на удаление всех записей из таблицы
    c.execute("DELETE FROM tender")

    # Сохранение изменений в базе данных
    conn.commit()

    # Закрываем соединение с базой данных
    conn.close()
# if __name__ == "__main__":
#     # print('Вставьте ссылку на тендер:')
#     # url_tender = input("")
#     # get_tender(url_tender)
#     # get_json_tender()
#     pars_tender()
# # print('Введите пароль')
# # passw = getpass.getpass("")
# # if passw == '12345677':
while True:
    # Запрос ввода от пользователя
    print('Введите 1 для загрузки нового тендера'
          '\nВведите 2 для запуска обновления всех тендеров'
          '\nВведите 3 для загрузки в Google Таблицу'
          '\nВведите 0 для закрытия программы')
    user_input = int(input("Выберите действие: "))

    if user_input == 1:
        creative_temp_folders()
        print('Вставьте ссылку на тендер:')
        url_tender = input("")
        get_tender(url_tender)
        get_json_tender()
        pars_tender()
        clear_to_sheet()
        write_to_sheet()
    elif user_input == 777:
        print('Введите пароль для очистки таблицы')
        passw = getpass.getpass("")
        if passw == 'prozorro':
            print("Вы удалите все данные в БД\nдействительно хотите этого?"
                  "\n1 - если да"
                  "\n0 - ЗАЧЕМ ВООБЩЕ ТУДА ПОЛЕЗЛИ")
            clean_sql = int(input("Выберите действие: "))
            if clean_sql == 1:
                clean_sql_table()
            elif clean_sql == 0:
                print("Программа завершена.")
                break  # Выход из цикла, завершение программы

    elif user_input == 2:
        update_tenders_from_json()
        clear_to_sheet()
        write_to_sheet()
    elif user_input == 3:
        clear_to_sheet()
        write_to_sheet()
    elif user_input == 0:
        print("Программа завершена.")
        break  # Выход из цикла, завершение программы
    else:
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
