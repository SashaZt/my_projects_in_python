import time
from datetime import datetime
from pathlib import Path

import pandas as pd

# Путь к CSV файлу и папке с HTML файлами
csv_file = "data/all_edrs.csv"
html_folder = "html_files"

# Чтение только нужной колонки из CSV
df = pd.read_csv(csv_file, usecols=["url"])

# Извлечение кодов EDR из URL с помощью vectorized операции
edr_codes = set(df["url"].str.split("/").str[-1])

# Получение списка HTML файлов с использованием pathlib
html_files = {f.stem.split("_edr_")[1] for f in Path(html_folder).glob("*.html")}

# Нахождение отсутствующих файлов с помощью разности множеств
missing_edr_codes = edr_codes - html_files

print(f"Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
# Вывод количества отсутствующих файлов
print(f"Количество отсутствующих файлов: {len(missing_edr_codes)}")
