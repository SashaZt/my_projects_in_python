from bs4 import BeautifulSoup
import glob


def parsing_url_html():
    targetPattern = r"C:\scrap_tutorial-master\Temp\html\*.html"
    files_html = glob.glob(targetPattern)
    urls = []
    ajax = []
    for item in files_html:
        with open(item, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        div_list = soup.find_all('div', {'class': 'gallery-vertical-item-valign'})

        # печать найденных элементов div
        for div in div_list:
            i = div.find('img').get('src')
            print(i)