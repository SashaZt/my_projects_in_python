import requests
from bs4 import BeautifulSoup


# Нажатие клавиш
# from selenium.webdriver.common.keys import Keys


# Для работы с драйвером селениум по Хром необходимо эти две строчки

# options = webdriver.ChromeOptions()
# options.add_argument(
#     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
# )
# # Отключение режима WebDriver
# options.add_argument("--disable-blink-features=AutomationControlled")


# # Работа в фоновом режиме
# options.headless = True
# # Настройка WEB драйвера
# driver_service = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
# driver = webdriver.Chrome(
#     service=driver_service,
#     options=options
# )
# # Окно браузера на весь экран
# driver.maximize_window()


def get_content(url):
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    }

    for i in range(0, 1):
        # Перебираем все ссылки
        resp = requests.get(url + f"?page={i}", headers=header)
        # time.sleep(randint(1, 5))
        try:
            soup = BeautifulSoup(resp.text, 'lxml')
            table = soup.find('div', attrs={'class': 'product-grid active'})
            table_card = table.find_all('div', attrs={'class': 'col-sm-4 col-xs-6'})
            # driver.implicitly_wait(5)
            for item in table_card:
                product_name = item.find('div', attrs={"class": "name"}).text.strip()
                product_price = item.find('div', attrs={"class": "price"}).text.strip()
                product_logo = item.find('div', attrs={"class": "image"}).find('img').get("data-echo")


                print(product_name, product_price, product_logo)

        except Exception as ex:
            print(ex)
        finally:
            pass
            # driver.close()
            # driver.quit()


def parse_content():
    url = "https://brandinhand.com.ua/zhenskaya-odezhda/?limit=100"
    get_content(url)


if __name__ == '__main__':
    parse_content()
