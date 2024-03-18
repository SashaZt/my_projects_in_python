from selenium import webdriver
# Нажатие клавиш
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import pickle
from aut_data import olx_pass, olx_email

def get_source_html(url):
    # Для работы с драйвером селениум по Хром необходимо эти две строчки
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = webdriver.ChromeOptions()
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    )
    # Отключение режима WebDriver
    options.add_argument("--disable-blink-features=AutomationControlled")
    # # Работа в фоновом режиме
    # options.headless = True
    # Настройка WEB драйвера
    driver_service = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")

    driver = webdriver.Chrome(
        service=driver_service,
        options=options
    )
    # Окно браузера на весь экран
    driver.maximize_window()

    try:
        driver.get(url=url)
        time.sleep(5)

    except Exception as ex:
        print(ex)

    finally:
        driver.close()
        driver.quit()

def main():
    get_source_html(url="https://www.olx.ua/d/uk/nedvizhimost/kvartiry/prodazha-kvartir/zhitomir/?currency=USD&search%5Bfilter_enum_number_of_rooms_string%5D%5B0%5D=odnokomnatnye&search%5Bfilter_enum_apartments_object_type%5D%5B0%5D=secondary_market")

if __name__ == "__main__":
    main()

#
# try:
#     # #Процесс получение куков, вход на страницу, введение логина и пароля, получение файла куки
#     # driver.get("https://www.olx.ua/account/?ref%5B0%5D%5Baction%5D=myaccount&ref%5B0%5D%5Bmethod%5D=index")
#     # driver.implicitly_wait(10)
#     #
#     # email_input = driver.find_element('id', 'userEmail')
#     # email_input.clear()
#     # email_input.send_keys(olx_email)
#     # driver.implicitly_wait(10)
#     # email_pass_input = driver.find_element('id', 'userPass')
#     # email_pass_input.clear()
#     # email_pass_input.send_keys(olx_pass)
#     # driver.implicitly_wait(5)
#     #
#     # login_button = driver.find_element('id', 'se_userLogin').click()
#     # driver.implicitly_wait(10)
#     #
#     # button_clouse = driver.find_element(By.CLASS_NAME, 'css-spwpto').click()
#     # driver.implicitly_wait(10)
#     #
#     # # cookies
#     # pickle.dump(driver.get_cookies(), open(f"{olx_email}_cookies", "wb"))
#
#     # Вход используя куки которые мы сохранили выше
#     driver.get("https://www.olx.ua/d/nedvizhimost/kvartiry/prodazha-kvartir/zhitomir/")
#     time.sleep(5)
#
#     # for cookie in pickle.load(open(f"{olx_email}_cookies", "rb")):
#     #     driver.add_cookie(cookie)
#     # # driver.implicitly_wait(5)
#     # driver.refresh()
#     driver.implicitly_wait(5)
#     # Получение ссылки обявления
#     href = driver.find_elements(By.XPATH, '//a[@class="css-rc5s2u"]').get_attribute('href')
#
#     driver.implicitly_wait(5)
#     print(href)
#
#
#
#
# except Exception as ex:
#     print(ex)
#
# finally:
#     driver.close()
#     driver.quit()
