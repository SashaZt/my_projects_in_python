import pandas as pd

# Загрузите данные из файлов 01.csv и 02.csv
df_01 = pd.read_csv('01.csv', delimiter=';', header=None, names=['column1', 'column2', 'column3'])

df_02 = pd.read_csv('02.csv', delimiter=',', header=None, names=['name', 'email'])

# Проход по строкам файла df_02
for index, row in df_02.iterrows():
    # Получите значение из первой колонки (name)
    name_to_find = row['name']

    # Найдите соответствующую строку в df_01
    matching_row = df_01[df_01['column2'] == name_to_find]

    # Если найдено совпадение, обновите значение в третьей колонке (column3)
    if not matching_row.empty:
        email_value = row['email']
        df_01.at[matching_row.index[0], 'column3'] = email_value

# Сохраните обновленные данные обратно в 01.csv
df_01.to_csv('01.csv', sep=';', index=False)
