from selenium import webdriver
# Нажатие клавиш
#from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import pickle
from aut_data import olx_pass, olx_email

# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

options = webdriver.ChromeOptions()
options.add_argument(
    "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
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

try:
    # #Процесс получение куков, вход на страницу, введение логина и пароля, получение файла куки
    # driver.get("https://www.olx.ua/account/?ref%5B0%5D%5Baction%5D=myaccount&ref%5B0%5D%5Bmethod%5D=index")
    # driver.implicitly_wait(10)
    #
    # email_input = driver.find_element('id', 'userEmail')
    # email_input.clear()
    # email_input.send_keys(olx_email)
    # driver.implicitly_wait(10)
    # email_pass_input = driver.find_element('id', 'userPass')
    # email_pass_input.clear()
    # email_pass_input.send_keys(olx_pass)
    # driver.implicitly_wait(5)
    #
    # login_button = driver.find_element('id', 'se_userLogin').click()
    # driver.implicitly_wait(10)
    #
    # button_clouse = driver.find_element(By.CLASS_NAME, 'css-spwpto').click()
    # driver.implicitly_wait(10)
    #
    # # cookies
    # pickle.dump(driver.get_cookies(), open(f"{olx_email}_cookies", "wb"))

    # Вход используя куки которые мы сохранили выше
    driver.get("https://www.olx.ua/d/obyavlenie/prodam-novobudovu-IDQaFJ9.html")
    time.sleep(5)

    for cookie in pickle.load(open(f"{olx_email}_cookies", "rb")):
        driver.add_cookie(cookie)
    # driver.implicitly_wait(5)
    driver.refresh()
    driver.implicitly_wait(5)
    # Находим описание обьевления
    description = driver.find_element(By.CLASS_NAME, 'css-g5mtbi-Text').text
    driver.implicitly_wait(5)
    # Открывваем кнопку "Показать телефон"
    phone_show = driver.find_element(By.XPATH, '//button[@class="css-65ydbw-BaseStyles"]')
    driver.implicitly_wait(5)
    phone_show.click()
    driver.implicitly_wait(5)
    # Получаем телефон продавца
    contact_phone = driver.find_element(By.XPATH, '//a[@data-testid="contact-phone"]').text
    driver.implicitly_wait(5)
    name = driver.find_element(By.XPATH, '//h4[@class="css-1rbjef7-Text eu5v0x0"]').text
    print(description, contact_phone, name)







except Exception as ex:
    print(ex)

finally:
    driver.close()
    driver.quit()
