import pychrome
import time
from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument("--remote-debugging-port=8000")
chromedriver = webdriver.Chrome(chrome_options=options, executable_path='C:\\scrap_tutorial-master\\chromedriver.exe')


def outputstart(**kwargs):
    print("start ", kwargs)


driver = chromedriver

dev_tools = pychrome.Browser(url="http://localhost:8000")
tab = dev_tools.list_tab()[0]
tab.start()

url = 'https://google.com'

start = time.time()
driver.get(url)
tab.call_method("Network.emulateNetworkConditions",
                offline=False,
                latency=100,
                downloadThroughput=93750,
                uploadThroughput=31250,
                connectionType="wifi")

tab.call_method("Network.enable", _timeout=20)
tab.set_listener("Network.requestWillBeSent", outputstart)
