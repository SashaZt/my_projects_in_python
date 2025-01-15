import re

# Пример кода с импортами
code = """
import json
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
"""

# Функция для извлечения имен модулей
def extract_modules(code):
    pattern = r"^import (\S+)|^from (\S+) import"
    matches = re.findall(pattern, code, re.MULTILINE)
    modules = {match[0] or match[1] for match in matches}
    return modules

# Извлечение имен модулей
modules = extract_modules(code)

# Исключаем стандартные библиотеки
standard_libs = {
    "os", "sys", "re", "json", "math", "pathlib", "itertools", "collections",
    "datetime", "functools", "logging", "typing", "time", "argparse"
}
third_party_modules = modules - standard_libs

# Формируем команду для установки через pip
if third_party_modules:
    pip_command = "pip install " + " ".join(third_party_modules)
    print("Команда для установки модулей:", pip_command)
else:
    print("Не найдено модулей для установки.")
