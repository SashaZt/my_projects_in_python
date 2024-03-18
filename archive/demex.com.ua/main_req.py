from bs4 import BeautifulSoup
import glob
import csv


def parsing():
    folder = r'c:\DATA\demex\ua\*.html'
    files_html = glob.glob(folder)

    heandler = ['url_product', 'name_product', 'bread', 'price_new', 'images', 'desk_product', 'original_numbers', 'all_table_ajax']
    with open('data_ua.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(heandler)  # Записываем заголовки только один раз
        for item in files_html:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            try:
                url_product = soup.find('meta', attrs={'itemprop': 'url'}).get("content")
            except:
                url_product = None
            try:
                name_product = soup.find('h1', attrs={'class': 'title-item'}).text
            except:
                name_product = None
            try:
                categ_product = soup.find_all('span', attrs={'itemprop': 'name'})
            except:
                categ_product = None
            try:
                bread = categ_product[-2].text
            except:
                bread = None
            try:
                price_new = soup.find('span', attrs={'class': 'price-val'}).text
            except:
                price_new = None
            # Получаем ссылки на все фото и добавляем их в словарь
            all_link_img = []
            try:
                all_images = soup.find('div', attrs={'class': 'gallery_thums_list'}).find_all('div')
            except:
                all_images = None
            try:
                images = soup.find('div', attrs={'class': 'col-md-4 popup-gallery'}).find('div').find('a').find('img').get('data-image')
                all_link_img.append(images)
            except:
                images = None
            if all_images is not None:
                for h in all_images:
                    url_img = h.find('a').get('href')
                    all_link_img.append(url_img)
                # Обьеденяим их в одну сроку, разделитель указываем в начале
                link_img = " ; ".join(all_link_img)
            try:
                desk_product = soup.find('dl', attrs={'class': 'dl-horizontal dl-criteria m-no'})
                desk_product = str(desk_product)
            except:
                desk_product = None
            """Запись разметки в одну строку"""
            if desk_product:
                desk_product = desk_product.replace('\n', '').replace('\r', '').replace('\t', '')

            try:
                original_numbers_div = soup.find('div', attrs={'id': 'case_oem'})

            except:
                original_numbers_div= None

            try:
                original_numbers = [div.text for div in original_numbers_div.find_all('div', class_='col-md-2')]
            except:
                original_numbers = None

            all_table_ajax = []
            try:
                text_table_ajax = soup.find('div', attrs={'class': 'col-md-6 col-app'}).find('dl').find('dt').text.replace('\n', '').replace('\r', '').replace('\t', '').strip()
                all_table_ajax.append(text_table_ajax)
                table_ajax = soup.find('div', attrs={'class': 'col-md-6 col-app'}).find('dl').find_all('dd')
                for dd in table_ajax:
                    models = dd.find_all('span')
                    model_avto_element = dd.find('strong')
                    if model_avto_element is not None:
                        model_avto = model_avto_element.text
                        all_table_ajax.append(model_avto)
                    # if model_avto is not None:

                    for model in models:
                        model_name = model.get_text().strip(' -')
                        all_table_ajax.append(model_name)
            except:
                pass


            values = [url_product, name_product, bread, price_new, link_img, desk_product, original_numbers, all_table_ajax]
            writer.writerow(values)


if __name__ == '__main__':
    parsing()
