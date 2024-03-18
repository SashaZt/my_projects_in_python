import glob
import os
import re

from bs4 import BeautifulSoup

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки

current_directory = os.getcwd()
temp_directory = 'temp'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
list_path = os.path.join(temp_path, 'list')
product_path = os.path.join(temp_path, 'product')


def delete_old_data():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, list_path, product_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Удалите файлы из папок list и product
    for folder in [list_path, product_path]:
        files = glob.glob(os.path.join(folder, '*'))
        for f in files:
            if os.path.isfile(f):
                os.remove(f)
        # print(f'Очистил папку {os.path.basename(folder)}')


# # Получаем все ссылки на необходимый товар
# def save_link_all_product(url):
#     header = {
#         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
#         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
#
#     }
#     product_url = []
#     resp = requests.get(url, headers=header)
#     soup = BeautifulSoup(resp.text, 'lxml')
#     regex_table = re.compile('slick-slide*')
#     urls = soup.find_all('div', attrs={'class': 'col col-9 text-truncate'})
#     for i in urls:
#         product_url.append(
#             {'url_name': f'https://uk.tgstat.com/{i.find("a").get("href")}'}
#         )
#         with open(f"url_category.json", 'w') as file:
#             json.dump(product_url, file, indent=4, ensure_ascii=False)
#
#
# # Сохраняем товар в html файл
# def save_category_html():
#     header = {
#         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
#         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
#
#     }
#     with open(f"url_category.json") as file:
#         all_site = json.load(file)
#     driver = get_chromedriver(use_proxy=False,
#                               user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")
#     for item in all_site:
#
#         driver.maximize_window()
#         driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
#         category = driver.find_element(By.XPATH, '//h1[@class="text-dark mt-2 text-center"]').text
#         # Листать по страницам ---------------------------------------------------------------------------
#         isNextDisable = False
#         while not isNextDisable:
#             try:
#                 driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
#                 driver.implicitly_wait(2)
#                 next_button = driver.find_element(By.XPATH,
#                                                   '//button[@class="btn btn-light border lm-button py-1 min-width-220px"]')
#                 # Проверка на наличие кнопки следующая страница, если есть, тогда листаем!
#                 if next_button:
#                     next_button.click()
#                     driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
#                     driver.implicitly_wait(2)
#                 else:
#                     isNextDisable = True
#             except:
#                 isNextDisable = True
#         # Листать по страницам ---------------------------------------------------------------------------
#         with open(f"data_{category}.html", "w", encoding='utf-8') as fl:
#             fl.write(driver.page_source)
#     driver.close()
#     driver.quit()
#
#
# def pasing_html():
#     datas = []
#     targetPattern = r"C:\\scrap_tutorial-master\\tgstat.ru\\*.html"
#     files_html = glob.glob(targetPattern)
#     url_category = []
#     for item in files_html:
#
#         group = item.split("\\")[-1].replace('.html', '')
#         driver = get_chromedriver(use_proxy=False,
#                                   user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")
#         # driver.maximize_window()
#         driver.get(item)  # 'url_name' - это и есть ссылка
#         driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
#         urls = driver.find_elements(By.XPATH, '//div[@class="col-12 col-sm-6 col-md-4"]//a')
#         for i in urls:
#             url_category.append(
#                 {'url_name': i.get_attribute("href")}
#             )
#     df = pandas.DataFrame(url_category)
#     df.to_csv(f"url_all.csv", sep=',', index=False)
#     # with open(f"url_all.json", 'a') as file:
#     #     json.dump(url_category, file, indent=4, ensure_ascii=False)
#
#
# def pars_group_url():
#     # Получаем список файлов с сылками на товары
#     header = {
#         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
#         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
#
#     }
#     targetPattern = r"C:\\scrap_tutorial-master\\tgstat.ru\\*.json"
#     files_json = glob.glob(targetPattern)
#     # По очереди json файл открывает
#     # driver = get_chromedriver(use_proxy=False,
#     #                           user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")
#     for item in files_json[18:]:
#         group = item.split("\\")[-1].replace('.json', '')
#
#         data = []
#         with open(f"{item}") as file:
#             all_site = json.load(file)
#
#         # Внутри json файла открывает ссылки
#         for href_card in all_site:
#             resp = requests.get(href_card['url_name'], headers=header)
#             soup = BeautifulSoup(resp.text, 'lxml')
#             try:
#                 href_soup = soup.find('div', attrs={'class': 'text-center text-sm-left'}).find('a').get("href")
#             except:
#                 href_soup = href_card['url_name']
#
#             # driver.get(href_card['url_name'])  # 'url_name' - это и есть ссылка
#             # driver.maximize_window()
#             # href = driver.find_element(By.XPATH, '//div[@class="text-center text-sm-left"]//a').get_attribute("href")
#             with open(f"tg_.csv", "a", errors='ignore') as file:
#                 writer = csv.writer(file, delimiter=";", lineterminator="\r")
#                 writer.writerow((
#                     href_soup, group
#                 ))
#
#     # driver.close()
#     # driver.quit()


def parsing():
    """Парсим уже из готовых html страничек"""
    folder = os.path.join(product_path, '*.html')
    files_html = glob.glob(folder)

    for item in files_html:
        with open(item, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        try:
            name_tg = soup.find('h1', attrs={'class': 'text-dark text-center text-sm-left'})

        except:
            name_tg = None
        name_tg = re.sub(r'\s+', ' ', name_tg.get_text()).strip()
        try:
            category_tg = soup.find('div', attrs={'class': 'text-left text-sm-right'}).find('div', attrs={
                'class': 'mt-2'}).find('a')
        except:
            category_tg = None
        category_tg = re.sub(r'\s+', ' ', category_tg.get_text()).strip()
        try:
            geo_tg = soup.find('div', attrs={'class': 'mt-4'})
        except:
            geo_tg = None
        geo_tg = re.sub(r'\s+', ' ', geo_tg.get_text()).strip()

        print(name_tg)
        print(category_tg)
        print(geo_tg)


if __name__ == '__main__':
    # delete_old_data()
    # url = "https://uk.tgstat.com/"
    # save_link_all_product(url)
    # save_category_html()
    # ######################save_html(url)
    # pasing_html()
    # pars_group_url()
    parsing()
