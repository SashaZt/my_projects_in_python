from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Инициализация драйвера Chrome с использованием webdriver-manager через объект Service
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Максимизация окна для удобного наблюдения
driver.maximize_window()

# Открытие страницы
driver.get("https://www.browserstack.com/users/sign_in")

# Установка значений для полей по ID
driver.execute_script(
    "document.getElementById('user_email_login').value='rbc@xyz.com';")
sleep(5)  # Задержка для наблюдения

driver.execute_script(
    "document.getElementById('user_password').value='password';")
sleep(5)  # Задержка для наблюдения

# Клик по кнопке отправки формы
driver.execute_script("document.getElementById('user_submit').click();")
sleep(5)  # Задержка для наблюдения

# Вызов alert на странице
driver.execute_script("alert('enter correct login credentials to continue');")
sleep(5)  # Задержка для просмотра alert

# Скролл вниз до конца страницы
driver.execute_script("window.scrollBy(0, document.body.scrollHeight)")
sleep(5)  # Задержка для наблюдения

# Обновление страницы
driver.execute_script("location.reload()")
sleep(5)  # Задержка для наблюдения после перезагрузки

# Держим окно открытым, чтобы наблюдать за результатами
input("Нажмите Enter для закрытия браузера...")

# Закрытие браузера
driver.quit()
