import csv
import glob
import re

from bs4 import BeautifulSoup

# import undetected_chromedriver as webdriver
delta = '''
avtolampa
'''
delta_list = delta.strip().split("\n")


def parsing():
    for folders in delta_list:

        # folder = 'kreplenie_dlya_velosipeda_na_avto'
        name_files_ua = folders.replace('-', '_')
        try:
            file_name_ua = f"C:\\scrap_tutorial-master\\archive\\dok.ua\\heandler\\{name_files_ua}.html"
        except:
            file_name_ua = None

        name_files_rus = folders.replace('-', '_') + '_rus'
        file_name_rus = f"C:\\scrap_tutorial-master\\archive\\dok.ua\\heandler\\{name_files_rus}.html"
        try:
            with open(file_name_ua, encoding="utf-8") as file:
                src = file.read()
        except:
            print(folders)
            continue
        soup = BeautifulSoup(src, 'lxml')
        row_id = 1
        hedler_ua = []
        while True:
            element = soup.find('span', {'data-row-id': str(row_id)})
            if element:
                hedler_ua.append(element.text.strip())
                row_id += 1
            else:
                break
        hedler_ua = [re.sub(r',.*$', '', element) for element in hedler_ua]
        with open(file_name_rus, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        row_id = 1
        hedler_rus = []
        while True:
            element = soup.find('span', {'data-row-id': str(row_id)})
            if element:
                hedler_rus.append(element.text.strip())
                row_id += 1
            else:
                break
        hedler_rus = [re.sub(r',.*$', '', element) for element in hedler_rus]
        # Элементы для добавления в начало каждого списка
        art_ua = 'Артикул'
        ser_ua = 'Серія'
        art_rus = 'Артикул'
        ser_rus = 'Серия'

        # Добавляем элементы в начало списков
        hedler_ua.insert(0, ser_ua)
        hedler_ua.insert(0, art_ua)

        hedler_rus.insert(0, ser_rus)
        hedler_rus.insert(0, art_rus)

        # Объединяем списки
        heandler = []
        heandler.extend(hedler_ua)
        heandler.extend(hedler_rus)
        add = ['link_product', 'name_product_ua', 'name_product_rus', 'link_img', 'price_product', 'delivery_product']
        heandler = add + heandler
        """Если в ручную делаем heandler, тогда закоментировать все что сверху, оставить только ручной вариант"""
        # heandler = ['link_product', 'name_product_ua', 'name_product_rus', 'link_img', 'price_product',
        #             'delivery_product', 'Серія', 'Модель', 'Артикул', 'Тип', 'Призначення', 'Напруга',
        #             'Ступінь обслуговуваності', 'Тип кріплення', 'Ємність, (Агод)', 'Клеми', 'Плюсова клема',
        #             'Пусковий струм', 'Виконання корпуса', 'Днищеве кріплення', 'Довжина', 'Ширина', 'Висота',
        #             'Довжина x Ширина x Висота', 'Країна бренду', 'Місце виробництва', 'Гарантія', 'Серия', 'Модель',
        #             'Артикул', 'Тип', 'Назначение', 'Напряжение', 'Степень обслуживаемости', 'Тип крепления',
        #             'Емкость, Ач', 'Клеммы', 'Плюсовая клемма', 'Пусковой ток', 'Исполнение корпуса',
        #             'Днищевое крепление', 'Длина', 'Ширина', 'Высота', 'Длина x Ширина x Высота', 'Страна бренда',
        #             'Место производства', 'Гарантия']

        yield folders, heandler


# folders = 'bokorezy'
def main():
    for folders, heandler in parsing():
        folders = folders.replace('-', '_')

        folder_ua = fr'c:\DATA\dok_ua\products\{folders}\ua\*.html'
        folder_rus = fr'c:\DATA\dok_ua\products\{folders}\rus\*.html'
        files_html_ua = glob.glob(folder_ua)
        files_html_rus = glob.glob(folder_rus)

        with open(f'C:\\scrap_tutorial-master\\archive\\dok.ua\\data\\{folders}.csv', 'w', newline='',
                  encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=heandler, delimiter=";")
            writer.writeheader()  # Записываем заголовки только один раз
            for item_ua, item_rus in zip(files_html_ua, files_html_rus):
                row_dict = {}  # словарь для текущей строки
                with open(item_ua, encoding="utf-8") as file:
                    src = file.read()
                soup = BeautifulSoup(src, 'lxml')
                try:
                    name_product_ua = soup.find('div', attrs={'class': 'card-title-box'}).find('h1').text.replace("\n",
                                                                                                                  " ")
                except:
                    name_product_ua = None
                try:
                    link_product = soup.find('link', attrs={'hreflang': 'x-default'}).get('href')
                except:
                    link_product = None
                all_link_img = []
                try:
                    images = soup.select('div.card-gallery-big__item img')
                    for img in images:
                        all_link_img.append(img['data-big-image'])
                except:
                    images = None
                link_img = ",".join(all_link_img)

                try:
                    price_product = soup.find('span', attrs={'itemprop': 'price'}).text

                except:
                    price_product = None
                try:
                    delivery_product = soup.find('span', attrs={'class': 'customer-city-date'}).text

                except:
                    delivery_product = None

                row_dict['link_product'] = link_product
                row_dict['name_product_ua'] = name_product_ua
                row_dict['link_img'] = link_img
                row_dict['price_product'] = price_product
                row_dict['delivery_product'] = delivery_product

                try:
                    rows_ua = soup.select('tr.card-characts-list-item')
                    for row in rows_ua:
                        title_cell = row.select_one('td.card-characts-list-item__title span.mistake-char-title')
                        text_cell = row.select_one('td.card-characts-list-item__text')
                        if title_cell and text_cell:
                            title_text = title_cell.get_text().strip()
                            text_value = text_cell.get_text().strip()
                            if title_text in heandler:
                                row_dict[title_text] = text_value

                except:
                    print("Ошибка в разборе RUS файла")
                # values_rus = []
                with open(item_rus, encoding="utf-8") as file:
                    src = file.read()
                soup = BeautifulSoup(src, 'lxml')
                try:
                    name_product_rus = soup.find('div', attrs={'class': 'card-title-box'}).find('h1').text.replace("\n",
                                                                                                                   " ")
                except:
                    name_product_rus = None

                row_dict['name_product_rus'] = name_product_rus  # Добавляем значение для русского имени продукта

                try:
                    rows_rus = soup.select('tr.card-characts-list-item')
                    for row in rows_rus:
                        title_cell = row.select_one('td.card-characts-list-item__title span.mistake-char-title')
                        text_cell = row.select_one('td.card-characts-list-item__text')
                        if title_cell and text_cell:
                            title_text_rus = title_cell.get_text().strip()
                            text_value_rus = text_cell.get_text().strip()
                            if title_text_rus in heandler:
                                row_dict[title_text_rus] = text_value_rus
                except:
                    print("Ошибка в разборе RUS файла")

                writer.writerow(row_dict)

def link():
    folders = 'avtolampa'
    folder = fr'c:\DATA\dok_ua\products\{folders}\rus\*.html'
    files_html = glob.glob(folder)

    heandler = ['link_product', 'Цоколь', 'Количество в упаковке']
    with open('output.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(heandler)  # Записываем заголовки только один раз
        for item in files_html:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            link_product = soup.find('link', attrs={'hreflang': 'ru'}).get('href')

            # Инициализируем переменные для колонок "Цоколь" и "Количество в упаковке"
            socket_value = ''
            packaging_value = ''

            rows_rus = soup.select('tr.card-characts-list-item')
            for row in rows_rus:
                title_cell = row.select_one('td.card-characts-list-item__title span.mistake-char-title')
                text_cell = row.select_one('td.card-characts-list-item__text')
                if title_cell and text_cell:
                    title_text_rus = title_cell.get_text().strip()
                    text_value_rus = text_cell.get_text().strip()

                    # Проверяем, соответствует ли "title_text_rus" вашим условиям
                    if title_text_rus == 'Цоколь':
                        socket_value = text_value_rus
                    elif title_text_rus == 'Количество в упаковке':
                        packaging_value = text_value_rus

            # Записываем данные в CSV файл
            writer.writerow([link_product, socket_value, packaging_value])

if __name__ == '__main__':
    # main()
    link()