from bs4 import BeautifulSoup
import csv
import glob
import re
import requests
import json
import cloudscraper
import os
import time
import undetected_chromedriver as webdriver
from selenium.common.exceptions import TimeoutException
# from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv

PROXY_HOST = '37.233.3.100'
PROXY_PORT = 9999
PROXY_USER = 'proxy_alex'
PROXY_PASS = 'DbrnjhbZ88'
# proxies = {
#     'http': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
#     'https': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
# }
proxies = {"http": f"http://{PROXY_HOST}:{PROXY_PORT}", f"https": f"http://{PROXY_HOST}:{PROXY_PORT}"}
cookies = {
    'sorting_e': '""',
    'show_qs_e': 'vhc%3Acar',
    'bm_sz': '08C3CE4636CDBA44170238CDFB248042~YAAQF04SAtkwC6mIAQAAHaWErhRkLkJ2SQTaG/RfhkygDojSlrCwdWIKWaPVetpCa06wO9m+M6ROfsb6UB8uayL7nSqNvOMU9Ba5nAQnRBFByyR1ryJOKLXZkJSKbOayKJLMhIgezIRb19RHFLWkskB0RWbnOd/ORNNinTAuJE98F98zq+GKNAdsP5QDzJPPhTsAgGd+Y4jPKOzfcGQflVjrUZG+pg2MFBRrJ/9h+AEBRH65JpwEIvrMDyeoRqO/GsIeuAccB893aMpGNoV8cOO+6yKqaadPJ3+nD/YVeVqTmw==~3359297~4343106',
    'vi': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJjaWQiOiJkMTA0ZWZiMC1iMDc2LTQyNGMtOWVkYi00Y2E4ZmJlODg0NmIiLCJpYXQiOjE2ODY1NTUxMTAsImF1ZCI6W119.3xquMPMB2bL8BhIb0NNtKJGrs2MUrDtufT8Ryps9wO4',
    'mdeConsentDataGoogle': '1',
    'mdeConsentData': 'CPtQ6dmPtQ6dmEyAHARUDICgAP_AAELAAAYgJftX_H__bW9r8f7_aft0eY1P9_j77uQzDhfNs-4F3L_W_JwX52E7NF36tqoKmR4Eu3LBIUNlHNHUTVmwaokVryHsak2cpTNKJ6BEkHMRO2dYCF5umxtjeQKY5_p_d3fx2D-t_dv-39z3z81Xn3dZf-_0-PCde5_9Dfn9fRfb-9IP9_78v8v8_9_rk2_eX33_79_7_H9-f_876BecAcABQAIAAaABFACYAFsBeYBISAgAAsACoAGQAOAAiABkADwAIgATwAqgDDAH6AkQBkgDJwGXBoAgATADqgJEAZOIgCABMAOqAkQBk4qAEAEwBeYyAEAEwBeY6AmAAsACoAGQAOAAiABkADwAHwARAAngBVAC4AGIAYYA_QEiAMkAZOAy4hAJAAWABkAEQATAAqgBcADEAkQBk5KAWAAsADIAHAARAA8ACIAFUALgAYgEiAMnKQEQAFgAVAAyABwAEQAMgAeABEACeAFIAKoAYgB-gJEAZIAycBlw.YAAAAAAAD4AAAKcAAAAA',
    'mobile.LOCALE': 'de',
    '_pubcid': '031d23ac-91d4-45c5-bdaf-a580a513f34c',
    'bm_mi': '9077EF4394263865C5645983A32CD252~YAAQI04SAjGXTKuIAQAA38AOrxT6fDh5LWQkGM0XNcbZU450BnrLceABmMwj+T46rKqLKKdCn49OpzivNb0HRObVpHkKjdjeTYjudts3//Si8NkbRyEU8cQ9sra9wXZ3XZjhVhqhHySzcVFWEA70h4Bfh8c88xOSGUT7WWcvng7el1vGkxFf558Xfq54A+jIDoanLrNkLvjfN7dwD0N+AlhwTkUTXTYmQA+vjUrPzV5G0aWDdKv/a+H8dtSGhPWpNjcSk/Ng7tFyWnVvLYxUo0FXjqp7wY/CrB4EVCas/KLZgxTUJxSVOc8Y0nkZ~1',
    'ak_bmsc': '5285A84A95CC983BE9E9E762C78AB005~000000000000000000000000000000~YAAQI04SAqC+TKuIAQAAhC8PrxR/XhShOOaPXssdBQKLb3Ts1kfSHhSEYiLQsLVFWxGq7qtRhuQQjw2NoQWQJJwRaSYkZrGndAKmA2ULxpKRWsDd8OFJywJkQUuLzwVYTkguzIqbtJb8m6RY1UBAkZkVnCJupIkQmudR00OWrgaV6X21MqgWA3ZBioB71hv6cwBf5pppGMBYzrBLEVadzptk8OkyPm+Fx91uxTtgl8MVWZbKkgsl3fP8zrhMMupsX5Fzbss6uFMg+AW5+2ZojRH6EPkWaMgSq95dH7YqYnbNlZbH76H6bCOeQdgqZsOCXTb8DboH0IngECDHW01eY/u8Usa3F2oTlzbyzdLPzA+34veYQGw0odVqI/BY09lm4lO7YYqcJYlXTPcNqXVm05S0spy4Mq7UpChKG4Bg4wEMN4TW',
    'optimizelyEndUserId': 'oeu1686564203488r0.5856765966130291',
    'sec_cpt': '098FED3F2BFF881AC2A2FB988F3D170B~1~YAAQI04SAlfdTKuIAQAAwXwPrwmmKiOkYJvj1w5Xj/2irA6yiEjY892wghE/rziSZ0Zc5b8wSBDnriqNnertVfDXOA21jt7150BetxMF1doOdWkM9Uacfs1LmmLPdFZ4/wWsiqC2o00aiOm2kKKHihyNWaktyVVQU4+WrlQlDStaP4w14x7w1tXA0A7S02mQ46cLwXEvQ14/O2LKN+5kG0A4QEUYZlXBQ3WAtFxx/wgNvUYfgvRZf2w5gLNeeZxecjehVnXTxLKU3DYx/bcfTHr0jt6PMNcziLISQ7rOB/wEtkPybJ4rG3neBCdDPLkcWvBpsvJBfBYTNRm5QkLWlMzxCqb97x0MpbBY/RYTS1an9pP2cvCtqEfm2RRYoJnafMNpnAbDbrUXZPx261GbJ6deGFQIkpywnkqDN/ioWz900CAdyVS+Z56Vi5iu4eeEM/9nn9yULGmxpWWvZEfKVZnTPyEnH6Wf6PfJVo7Uj9Q0jZ54zengnngkErJIwnK5hGJOLhjBIYYutBegSVNCLhx3PpzPjTFoMJ8XIt7nudgl1tdMfRelGWOoSoWH2kydEfaXh/RBqAU33G5N0QKTnEUsbQ==',
    '_gid': 'GA1.2.334415945.1686564284',
    '__gsas': 'ID=d88321e0a0d5de34:T=1686564283:RT=1686564283:S=ALNI_MYNSuWiBDv5VuGduZMB08KT89sSxA',
    '_fbp': 'fb.1.1686564284026.738638940',
    '_gcl_au': '1.1.296932829.1686564284',
    'iom_consent': '0103ff0000&1686564284141',
    'FPID': 'FPID2.2.q2hBIeFqXOUBZuubT78%2FFZWE1uYK9bLg3i6NFyp%2Fy4Q%3D.1686564284',
    'FPLC': 'Dk2BGzUIgoyR06ftMJLZIyQHFCUL12mxKvWQ8fxYpv2Kla%2FGNvAub609S71WA5VW4HETyms5nsEzzR3da2xSYSmx%2Bo8DA1v72V%2F82rJsgpvkZfsNOX7bU1gM8ut5Aw%3D%3D',
    '_tt_enable_cookie': '1',
    '_ttp': '8X5w0OrxIZYF7nx_4E6_owNqi1_',
    'ioam2018': '000d422fb44c9d9ab6486edbb:1715853884142:1686564284142:.mobile.de:3:mobile:DE/DE/OB/S/P/S/G:noevent:1686564389455:bdta3l',
    '_abck': 'CB85C5387300E4D0FC14A9B5C7488542~0~YAAQI04SAgv2TauIAQAA80ISrwrJSb36kDt5l+zT/q363h3rR0pNFNChiP+YRMqnFi4yoifqntNH10s9mEnA1ATIv8sBBeipdE9TiB4cRK40enb3beeaY+nROJgBwuPW/VNjslEZCfrZEcTORjEVLlmMqAkqIteIi9ZeZQGwVPoCwNEW4/4k0jrVWAIVunqr2nRW0UFisVbNkhvrew9oCK3IE+31HdsLPrHCuPjHYW9qqaSUwZmhnS65S250X89ZrM4OoxeAcp8WmNlxmnXYZSwLaVfnLTxR881zZZhdi3I9O5luTi74/425NBRoahGiavyhEoqvBOTznZ2xqobaBVip9Jg53Ns3z5FdG8nXsJ+hq7AgnczLprYgTahRFEm/aVaqDu7MAOJlxH7cXOVr1U2sSByzhM8=~-1~||-1||~-1',
    '_uetsid': '8e8aa680090811eeadf5499d80ae2d6e',
    '_uetvid': '8e8ad980090811eebdc88b3b485564d3',
    'cto_bundle': 'pRqozF90SDFQdGdpbWZmQnhCUSUyQkRoTEtHT1BWRGxyM3FiVHZ5cUtQbjVra0xDd3ZMenFWc2prcHB1SXg3dW9VMlN5QTY0dmdHUkV2bXVwUCUyRkYwdzFRVzJLSlElMkJ4Q2k5Rjh1cHBQU3UzZW9QZ0dPcmhKQm1MUWRQRmFJZGhTYk03bFZEeWJwNlBlQXdLNU1GZG5hdlZwQ3cyQVElM0QlM0Q',
    '_ga': 'GA1.2.1171363062.1686564284',
    '_ga_2KLM51DVJQ': 'GS1.1.1686564284.1.1.1686564512.0.0.0',
    '_ga_2H40T2VTNP': 'GS1.1.1686564284.1.1.1686564512.0.0.0',
    'bm_sv': 'D0D68FE24346CD64EEB0E80237913B35~YAAQI04SArEwUKuIAQAAt0EXrxT8nc6okPF2X8sGCeAnSVCUe2wyPI/bEwgo1DSTzKqclmMCEVNZKHFha/dKJXp4FgJ1BVYbi/cBNHtQsHNDeHR7jhLdLKMuujcxMZuLTMcfuFURFL2U8/CR1O3UB8/B/qjrt2WMgDmCOWA5/0RUW3ZUmNjut6lo8ivI18pwwP+2/LKqL5s/Pue6gcyAMKfRIc/CdgJhG3d4ujtbgFmNf6SSdFVeV8W/ROxDrJPA~1',
}

headers = {
    'authority': 'www.mobile.de',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'no-cache',
    # 'cookie': 'sorting_e=""; show_qs_e=vhc%3Acar; bm_sz=08C3CE4636CDBA44170238CDFB248042~YAAQF04SAtkwC6mIAQAAHaWErhRkLkJ2SQTaG/RfhkygDojSlrCwdWIKWaPVetpCa06wO9m+M6ROfsb6UB8uayL7nSqNvOMU9Ba5nAQnRBFByyR1ryJOKLXZkJSKbOayKJLMhIgezIRb19RHFLWkskB0RWbnOd/ORNNinTAuJE98F98zq+GKNAdsP5QDzJPPhTsAgGd+Y4jPKOzfcGQflVjrUZG+pg2MFBRrJ/9h+AEBRH65JpwEIvrMDyeoRqO/GsIeuAccB893aMpGNoV8cOO+6yKqaadPJ3+nD/YVeVqTmw==~3359297~4343106; vi=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJjaWQiOiJkMTA0ZWZiMC1iMDc2LTQyNGMtOWVkYi00Y2E4ZmJlODg0NmIiLCJpYXQiOjE2ODY1NTUxMTAsImF1ZCI6W119.3xquMPMB2bL8BhIb0NNtKJGrs2MUrDtufT8Ryps9wO4; mdeConsentDataGoogle=1; mdeConsentData=CPtQ6dmPtQ6dmEyAHARUDICgAP_AAELAAAYgJftX_H__bW9r8f7_aft0eY1P9_j77uQzDhfNs-4F3L_W_JwX52E7NF36tqoKmR4Eu3LBIUNlHNHUTVmwaokVryHsak2cpTNKJ6BEkHMRO2dYCF5umxtjeQKY5_p_d3fx2D-t_dv-39z3z81Xn3dZf-_0-PCde5_9Dfn9fRfb-9IP9_78v8v8_9_rk2_eX33_79_7_H9-f_876BecAcABQAIAAaABFACYAFsBeYBISAgAAsACoAGQAOAAiABkADwAIgATwAqgDDAH6AkQBkgDJwGXBoAgATADqgJEAZOIgCABMAOqAkQBk4qAEAEwBeYyAEAEwBeY6AmAAsACoAGQAOAAiABkADwAHwARAAngBVAC4AGIAYYA_QEiAMkAZOAy4hAJAAWABkAEQATAAqgBcADEAkQBk5KAWAAsADIAHAARAA8ACIAFUALgAYgEiAMnKQEQAFgAVAAyABwAEQAMgAeABEACeAFIAKoAYgB-gJEAZIAycBlw.YAAAAAAAD4AAAKcAAAAA; mobile.LOCALE=de; _pubcid=031d23ac-91d4-45c5-bdaf-a580a513f34c; bm_mi=9077EF4394263865C5645983A32CD252~YAAQI04SAjGXTKuIAQAA38AOrxT6fDh5LWQkGM0XNcbZU450BnrLceABmMwj+T46rKqLKKdCn49OpzivNb0HRObVpHkKjdjeTYjudts3//Si8NkbRyEU8cQ9sra9wXZ3XZjhVhqhHySzcVFWEA70h4Bfh8c88xOSGUT7WWcvng7el1vGkxFf558Xfq54A+jIDoanLrNkLvjfN7dwD0N+AlhwTkUTXTYmQA+vjUrPzV5G0aWDdKv/a+H8dtSGhPWpNjcSk/Ng7tFyWnVvLYxUo0FXjqp7wY/CrB4EVCas/KLZgxTUJxSVOc8Y0nkZ~1; ak_bmsc=5285A84A95CC983BE9E9E762C78AB005~000000000000000000000000000000~YAAQI04SAqC+TKuIAQAAhC8PrxR/XhShOOaPXssdBQKLb3Ts1kfSHhSEYiLQsLVFWxGq7qtRhuQQjw2NoQWQJJwRaSYkZrGndAKmA2ULxpKRWsDd8OFJywJkQUuLzwVYTkguzIqbtJb8m6RY1UBAkZkVnCJupIkQmudR00OWrgaV6X21MqgWA3ZBioB71hv6cwBf5pppGMBYzrBLEVadzptk8OkyPm+Fx91uxTtgl8MVWZbKkgsl3fP8zrhMMupsX5Fzbss6uFMg+AW5+2ZojRH6EPkWaMgSq95dH7YqYnbNlZbH76H6bCOeQdgqZsOCXTb8DboH0IngECDHW01eY/u8Usa3F2oTlzbyzdLPzA+34veYQGw0odVqI/BY09lm4lO7YYqcJYlXTPcNqXVm05S0spy4Mq7UpChKG4Bg4wEMN4TW; optimizelyEndUserId=oeu1686564203488r0.5856765966130291; sec_cpt=098FED3F2BFF881AC2A2FB988F3D170B~1~YAAQI04SAlfdTKuIAQAAwXwPrwmmKiOkYJvj1w5Xj/2irA6yiEjY892wghE/rziSZ0Zc5b8wSBDnriqNnertVfDXOA21jt7150BetxMF1doOdWkM9Uacfs1LmmLPdFZ4/wWsiqC2o00aiOm2kKKHihyNWaktyVVQU4+WrlQlDStaP4w14x7w1tXA0A7S02mQ46cLwXEvQ14/O2LKN+5kG0A4QEUYZlXBQ3WAtFxx/wgNvUYfgvRZf2w5gLNeeZxecjehVnXTxLKU3DYx/bcfTHr0jt6PMNcziLISQ7rOB/wEtkPybJ4rG3neBCdDPLkcWvBpsvJBfBYTNRm5QkLWlMzxCqb97x0MpbBY/RYTS1an9pP2cvCtqEfm2RRYoJnafMNpnAbDbrUXZPx261GbJ6deGFQIkpywnkqDN/ioWz900CAdyVS+Z56Vi5iu4eeEM/9nn9yULGmxpWWvZEfKVZnTPyEnH6Wf6PfJVo7Uj9Q0jZ54zengnngkErJIwnK5hGJOLhjBIYYutBegSVNCLhx3PpzPjTFoMJ8XIt7nudgl1tdMfRelGWOoSoWH2kydEfaXh/RBqAU33G5N0QKTnEUsbQ==; _gid=GA1.2.334415945.1686564284; __gsas=ID=d88321e0a0d5de34:T=1686564283:RT=1686564283:S=ALNI_MYNSuWiBDv5VuGduZMB08KT89sSxA; _fbp=fb.1.1686564284026.738638940; _gcl_au=1.1.296932829.1686564284; iom_consent=0103ff0000&1686564284141; FPID=FPID2.2.q2hBIeFqXOUBZuubT78%2FFZWE1uYK9bLg3i6NFyp%2Fy4Q%3D.1686564284; FPLC=Dk2BGzUIgoyR06ftMJLZIyQHFCUL12mxKvWQ8fxYpv2Kla%2FGNvAub609S71WA5VW4HETyms5nsEzzR3da2xSYSmx%2Bo8DA1v72V%2F82rJsgpvkZfsNOX7bU1gM8ut5Aw%3D%3D; _tt_enable_cookie=1; _ttp=8X5w0OrxIZYF7nx_4E6_owNqi1_; ioam2018=000d422fb44c9d9ab6486edbb:1715853884142:1686564284142:.mobile.de:3:mobile:DE/DE/OB/S/P/S/G:noevent:1686564389455:bdta3l; _abck=CB85C5387300E4D0FC14A9B5C7488542~0~YAAQI04SAgv2TauIAQAA80ISrwrJSb36kDt5l+zT/q363h3rR0pNFNChiP+YRMqnFi4yoifqntNH10s9mEnA1ATIv8sBBeipdE9TiB4cRK40enb3beeaY+nROJgBwuPW/VNjslEZCfrZEcTORjEVLlmMqAkqIteIi9ZeZQGwVPoCwNEW4/4k0jrVWAIVunqr2nRW0UFisVbNkhvrew9oCK3IE+31HdsLPrHCuPjHYW9qqaSUwZmhnS65S250X89ZrM4OoxeAcp8WmNlxmnXYZSwLaVfnLTxR881zZZhdi3I9O5luTi74/425NBRoahGiavyhEoqvBOTznZ2xqobaBVip9Jg53Ns3z5FdG8nXsJ+hq7AgnczLprYgTahRFEm/aVaqDu7MAOJlxH7cXOVr1U2sSByzhM8=~-1~||-1||~-1; _uetsid=8e8aa680090811eeadf5499d80ae2d6e; _uetvid=8e8ad980090811eebdc88b3b485564d3; cto_bundle=pRqozF90SDFQdGdpbWZmQnhCUSUyQkRoTEtHT1BWRGxyM3FiVHZ5cUtQbjVra0xDd3ZMenFWc2prcHB1SXg3dW9VMlN5QTY0dmdHUkV2bXVwUCUyRkYwdzFRVzJLSlElMkJ4Q2k5Rjh1cHBQU3UzZW9QZ0dPcmhKQm1MUWRQRmFJZGhTYk03bFZEeWJwNlBlQXdLNU1GZG5hdlZwQ3cyQVElM0QlM0Q; _ga=GA1.2.1171363062.1686564284; _ga_2KLM51DVJQ=GS1.1.1686564284.1.1.1686564512.0.0.0; _ga_2H40T2VTNP=GS1.1.1686564284.1.1.1686564512.0.0.0; bm_sv=D0D68FE24346CD64EEB0E80237913B35~YAAQI04SArEwUKuIAQAAt0EXrxT8nc6okPF2X8sGCeAnSVCUe2wyPI/bEwgo1DSTzKqclmMCEVNZKHFha/dKJXp4FgJ1BVYbi/cBNHtQsHNDeHR7jhLdLKMuujcxMZuLTMcfuFURFL2U8/CR1O3UB8/B/qjrt2WMgDmCOWA5/0RUW3ZUmNjut6lo8ivI18pwwP+2/LKqL5s/Pue6gcyAMKfRIc/CdgJhG3d4ujtbgFmNf6SSdFVeV8W/ROxDrJPA~1',
    'dnt': '1',
    'pragma': 'no-cache',
    'referer': 'https://www.mobile.de/ru/%D0%BA%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F/%D0%B0%D0%B2%D1%82%D0%BE%D0%BC%D0%BE%D0%B1%D0%B8%D0%BB%D1%8C/vhc:car,slt:dealer,doc:7,vcg:',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}



def get_undetected_chromedriver():
    # Обход защиты
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
    # chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--proxy-server=45.14.174.253:80")
    # chrome_options.add_argument('--ignore-certificate-errors')
    # chrome_options.add_argument('--ignore-ssl-errors')
    # chrome_options.add_argument('--disable-extensions')
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-setuid-sandbox')
    # driver = webdriver.Chrome(options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)

    return driver


def get_requests():
    response = requests.get(
        'https://www.mobile.de/ru/%D0%BA%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F/%D0%B0%D0%B2%D1%82%D0%BE%D0%BC%D0%BE%D0%B1%D0%B8%D0%BB%D1%8C/vhc:car,pgn:1,pgs:50,slt:dealer,doc:7',
        cookies=cookies,
        headers=headers,
    )
    src = response.text
    soup = BeautifulSoup(src, 'lxml')
    filename = f"data.html"
    with open(filename, "w", encoding='utf-8') as file:
        file.write(src)


def parsing_pagination():
    file = f"data.html"
    with open(file, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    regex = re.compile('^list-entry g-row.*')
    urls= soup.find_all('article', attrs={'class': regex})
    all_urls = []
    for u in urls:
        url = 'https://www.mobile.de' + u.find('a').get('href')
        all_urls.append(url)
    for i in all_urls[:1]:
        response = requests.get(
            i,
            cookies=cookies,
            headers=headers,
        )
        src = response.text
        filename = f"avto.html"
        with open(filename, "w", encoding='utf-8') as file:
            file.write(src)
def parsing():
    file = f"avto.html"
    with open(file, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    name = soup.find('h1', attrs={'class': 'h2 g-col-8'}).text
    all_price =soup.find('div', attrs={'class': 'header-price-box g-col-4'})
    price_b = ''
    price_n = ''

    if all_price:
        soup_price = BeautifulSoup(str(all_price), 'lxml')
    else:
        print("Цена не найдена.")
    for box in soup_price:
        prices = box.find_all('p')
        for price in prices:
            value = price.text.strip()
            if 'Брутто' in value:
                price_b = value.replace(" € (Брутто)", "")
            if 'Нетто' in value:
                price_n = value.replace(" € (Нетто)", "")
            # print(value.replace(" € (Брутто)", "").replace(" € (Нетто)", ""))

    photos = soup.find('div', attrs={'class': 'image-gallery-wrapper js-vip-gallery'}).find_all('div', attrs={'class': 'gallery-bg js-gallery-img js-load-on-demand'})
    for j in photos:
        print(j.get('data-src'))
    # print(photos)


    # print(all_price)

def get_cloudscraper():
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False

    })
    r = scraper.get(
        'https://sellercentral.amazon.com/skucentral?mSku=AV-QNMH-TN28&ref=myi_skuc', cookies=cookies,
        headers=headers
    )  # , proxies=proxies
    html = r.content
    filename = f"amazon.html"
    with open(filename, "w", encoding='utf-8') as f:
        f.write(html.decode('utf-8'))



if __name__ == '__main__':
    # get_requests()
    # get_cloudscraper()
    # get_selenium()
    parsing()
