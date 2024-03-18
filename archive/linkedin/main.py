import undetected_chromedriver as uc
import time
import pickle

driver = uc.Chrome()
driver.get('https://www.linkedin.com/')
# # Блок работы с куками-----------------------------------------
# # Создание куки
# time.sleep(30)
# pickle.dump(driver.get_cookies(), open("cookies", "wb"))
# # Читание куки
for cookie in pickle.load(open("cookies", "rb")):
    driver.add_cookie(cookie)
# # Блок работы с куками-----------------------------------------
time.sleep(1)
driver.refresh()
time.sleep(10)
driver.close()
driver.quit()
