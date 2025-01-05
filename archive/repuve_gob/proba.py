import time

import requests
import selenium

# selenium-wire import
from seleniumwire import webdriver

# webdriver manager import
from webdriver_manager.chrome import ChromeDriverManager

# selenium imports
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains

"""
for next week:
add a wait for thumbnail to be clickable - due to page load strategy being eager
capture the url of the m3u8 file
have it run through the m3u8 parser
look through the featured video files on the watch page to verify they are functional
"""
# create the new instance of the driver


should_run_locally = False
if should_run_locally is True:
    options = Options()
    options.add_experimental_option("detach", True)
    options.page_load_strategy = "eager"
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=options
    )
else:
    sw_options = {"addr": "127.0.0.1", "auto_config": False, "port": 8091}
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--proxy-server=host.docker.internal:8091")
    chrome_options.add_argument("--ignore-certificate-errors")
    driver = webdriver.Remote(
        command_executor="127.0.0.1:4444",
        options=chrome_options,
        seleniumwire_options=sw_options,
    )

# driver.scopes = [
#     '.*cloudfront.net/.*/playlist.m3u8',
# ]

driver.implicitly_wait(15)
driver.maximize_window()
# navigate to a video on the Flo Grappling site
driver.get("https://www.flograppling.com")
time.sleep(10)
for request in driver.requests:
    if request.response:
        # set the captured m3u8 file as the manifest uri variable
        print(
            request.url,
            request.response.status_code,
            request.response.headers["Content-Type"],
        )
