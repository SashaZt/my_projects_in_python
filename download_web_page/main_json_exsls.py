# Необходимые библиотеки
import json  # Для работы с JSON файлами

import pandas as pd  # Для работы с таблицами и Excel

# Название JSON файла
json_result = "result.json"

# Открыть и прочитать JSON файл
with open(json_result, encoding="utf-8") as file:
    # Прочитать содержимое JSON файла
    data = json.load(file)

# Создание DataFrame из данных JSON
df = pd.DataFrame(data)

# Экспорт в Excel
df.to_excel("output.xlsx", index=False, sheet_name="Data")
