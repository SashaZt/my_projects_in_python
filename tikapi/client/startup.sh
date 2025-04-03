#!/bin/bash

# Перезапись cron заданий с использованием переменных окружения
echo "# TikTok API Client cron jobs" > /etc/cron.d/tiktok_cron
echo "${HOURLY_SCHEDULE:-0 */4 * * *} /usr/local/bin/python /app/main_four_tik_tok.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/tiktok_cron
echo "${DAILY_SCHEDULE:-0 0 * * *} /usr/local/bin/python /app/main_once_day_tik_tok.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/tiktok_cron

# Установка прав и обновление cron задач
chmod 0644 /etc/cron.d/tiktok_cron
crontab /etc/cron.d/tiktok_cron

# Запуск cron демона в фоне
cron

# Создание необходимых директорий если они еще не существуют
mkdir -p data/temp data/user_info data/user_live_list data/user_live_analytics logs

# Инициализация настроек на основе переменных окружения
python -c "
import json
import os

# Путь к файлу конфигурации
config_file = 'config.py'

# Формируем содержимое файла конфигурации
config_content = f'''
# Автоматически сгенерированный файл настроек
# Не редактируйте вручную - будет перезаписан при перезапуске контейнера

import os
from pathlib import Path

# Базовые настройки API
API_BASE_URL = '{os.environ.get('API_BASE_URL', 'http://api:5000/api')}'
API_TIMEOUT = {os.environ.get('API_TIMEOUT', '30')}
API_MAX_RETRIES = {os.environ.get('API_MAX_RETRIES', '10')}
API_RETRY_DELAY = {os.environ.get('API_RETRY_DELAY', '5')}

# Директории для данных
DATA_DIR = Path('./data')
TEMP_DIR = DATA_DIR / 'temp'
USER_INFO_DIR = DATA_DIR / 'user_info'
USER_LIVE_LIST_DIR = DATA_DIR / 'user_live_list'
USER_LIVE_ANALYTICS_DIR = DATA_DIR / 'user_live_analytics'

# Путь к файлу с данными пользователей
USER_JSON_FILE = DATA_DIR / 'users.json'

# Настройки логирования
LOG_LEVEL = '{os.environ.get('LOG_LEVEL', 'INFO')}'
LOG_FORMAT = '%(asctime)s | %(levelname)s | %(lineno)d | %(message)s'
'''

# Записываем в файл
with open(config_file, 'w') as f:
    f.write(config_content)

print(f'Конфигурация записана в {config_file}')
"

# Создаем пример файла с пользователями, если он не существует
if [ ! -f /app/data/users.json ]; then
  echo "Создаем пример файла с пользователями..."
  echo '[
    {
      "account_key": "example_key_1",
      "tik_tok_id": "example_id_1"
    },
    {
      "account_key": "example_key_2",
      "tik_tok_id": "example_id_2"
    }
  ]' > /app/data/users.json
fi

# Вывод информации о запуске
echo "============================================"
echo "TikTok API Client запущен в $(date)"
echo "Часовой пояс: ${TZ}"
echo "API: ${API_BASE_URL}"
echo "Cron задачи:"
echo "- Ежедневно (${DAILY_SCHEDULE:-0 0 * * *}): main_once_day_tik_tok.py"
echo "- Каждые 4 часа (${HOURLY_SCHEDULE:-0 */4 * * *}): main_four_tik_tok.py"
echo "============================================"

# Запуск задач при старте контейнера (если нужно)
if [ "${RUN_ON_START}" = "true" ]; then
  echo "Запускаем задачи при старте контейнера..."
  python /app/main_once_day_tik_tok.py &
  python /app/main_four_tik_tok.py &
fi

# Чтобы контейнер не завершался
tail -f /var/log/cron.log