import glob
import csv
from bs4 import BeautifulSoup

def main():
    folders = [r"C:\scrap_tutorial-master\lingerie_ua\data_html\*.html"]

    counter = 0
    for folder in folders:
        files_html = glob.glob(folder)
        with open('data.csv', mode='w', encoding='utf-8', newline='') as csv_file:
            fieldnames = ['Название', 'Артикул', 'Производство', 'Материал', 'Старая цена', 'Новая цена', 'Верх Одежды', 'Низ Одежды', 'Рукав Одежды', 'Состав', 'Бренд']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for item in files_html[:20]:
                with open(item, encoding="utf-8") as file:
                    src = file.read()
                counter += 1
                # print(f"{counter} из {len(files_html)}| {item}")
                soup = BeautifulSoup(src, 'lxml')

                name = soup.find('h1', attrs={'itemprop': 'name'}).text
                manufacturer_blocks = soup.find_all('ul', {'class': 'list-unstyled manufacturer'})
                price_new =  soup.find('span', {'class': 'price-new'}).text.strip()
                price_old = soup.find('span', {'class': 'price-new'}).text.strip()

                # Обрабатываем каждый блок
                for block in manufacturer_blocks:
                    # Инициализируем словарь с пустыми значениями для каждой колонки
                    row = {key: '' for key in fieldnames}

                    # Добавляем значений в словарь row

                    row['Название'] = name
                    row['Старая цена'] = price_new
                    row['Новая цена'] = price_old


                    # Ищем все элементы списка внутри блока
                    list_items = block.find_all('li')

                    # Обрабатываем каждый элемент списка
                    for item in list_items:
                        # Извлекаем текст из элемента
                        text = item.get_text(strip=True)

                        # Проверяем наличие ключевых слов и записываем значения в соответствующие колонки
                        if 'Артикул' in text:
                            row['Артикул'] = text.split(':')[1].strip()
                        elif 'Производство' in text:
                            row['Производство'] = text.split(':')[1].strip()
                        elif 'Материал' in text:
                            row['Материал'] = text.split(':')[1].strip()
                        elif 'Старая цена' in text:
                            row['Старая цена'] = text.split(':')[1].strip()
                        elif 'Новая цена' in text:
                            row['Новая цена'] = text.split(':')[1].strip()


                        elif 'Верх Одежды' in text:
                            row['Верх Одежды'] = text.split(':')[1].strip()
                        elif 'Низ Одежды' in text:
                            row['Низ Одежды'] = text.split(':')[1].strip()
                        elif 'Рукав Одежды' in text:
                            row['Рукав Одежды'] = text.split(':')[1].strip()
                        elif 'Состав' in text:
                            row['Состав'] = text.split(':')[1].strip()
                        elif 'Бренд' in text:
                            row['Бренд'] = item.find('a').get_text(strip=True)

                    # Записываем данные в файл csv
                    writer.writerow(row)






if __name__ == '__main__':
    main()
