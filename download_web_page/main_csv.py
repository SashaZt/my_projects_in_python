import pandas as pd

# Чтение CSV-файлов
analytics_df = pd.read_csv("daily_live_analytics_202505022340.csv", sep=";")
users_df = pd.read_csv("users_202505022340.csv", sep=";")

# Переименование столбца id в users_df для соответствия с user_id в analytics_df
users_df = users_df.rename(columns={"id": "user_id"})

# Объединение данных (left join)
merged_df = pd.merge(analytics_df, users_df, on="user_id", how="left")

# Сохранение результата в новый CSV-файл
merged_df.to_csv("merged_output.csv", sep=";", index=False)

print("Объединенный CSV-файл сохранен как 'merged_output.csv'")
