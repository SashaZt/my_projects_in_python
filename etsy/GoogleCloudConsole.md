# Инструкция по настройке Google Sheets API и Google Drive API

## Шаг 1: Создание проекта в Google Cloud Console

1. Перейдите на сайт [Google Cloud Console](https://console.cloud.google.com).
2. Войдите в свой аккаунт Google.
3. В верхнем меню выберите **"Select a Project"** (Выбор проекта) и нажмите на **"New Project"** (Создать проект).
4. Дайте проекту имя и, при необходимости, выберите организацию и местоположение.
5. Нажмите **"Create"** (Создать).

## Шаг 2: Включение Google Sheets API и Google Drive API

1. В меню слева выберите **API & Services** > **Library** (Библиотека API).
2. В строке поиска введите **Google Sheets API** и нажмите **Enter**.
3. Нажмите на найденный API и нажмите **"Enable"** (Включить).
4. Повторите то же самое для **Google Drive API**.

## Шаг 3: Создание учетных данных (Credentials)

1. Перейдите в **API & Services** > **Credentials** (Учетные данные) в меню слева.
2. Нажмите на кнопку **"Create Credentials"** (Создать учетные данные) и выберите **"Service Account"** (Учетная запись службы).
3. Дайте учетной записи службы имя и нажмите **"Create"** (Создать).
4. На следующем шаге выберите роль, которая имеет доступ к редактированию файлов Google Sheets. Например, можно выбрать роль **Editor** (Редактор).
5. Нажмите **"Continue"** (Продолжить), а затем **"Done"** (Готово).
6. В разделе **"Keys"** (Ключи) нажмите на **"Add Key"** (Добавить ключ) и выберите **JSON**.
7. Скачанный JSON-файл — это файл ключа, который потребуется для работы с API.

## Шаг 4: Дать доступ сервисному аккаунту к Google Sheets

1. Создайте или откройте документ Google Sheets по ссылке: [Google Sheets](https://sheets.google.com).
2. Нажмите **"Share"** (Поделиться) в правом верхнем углу.
3. Введите email-адрес сервисного аккаунта (он выглядит как `your-service-account@your-project-id.iam.gserviceaccount.com`), который был создан на шаге 3.
4. Выберите права доступа **Editor** (Редактор) и нажмите **"Send"** (Отправить).

## Шаг 5: Использование файла JSON для доступа к Google Sheets

Теперь у вас есть JSON-файл с учетными данными для доступа к Google Sheets через API. Его можно использовать в скрипте на Python или другом языке программирования для взаимодействия с таблицей.

Пример кода на Python для записи данных в Google Sheets:

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Настройка API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# Открытие таблицы и выбор листа
sheet = client.open('Название вашей таблицы').sheet1

# Запись данных в таблицу
sheet.update_cell(1, 1, "Hello, World!")  # Записываем данные в ячейку A1
