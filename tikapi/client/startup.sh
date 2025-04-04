#!/bin/bash

# Прямая запись в cron с правильными пробелами между частями
echo "# TikTok API Client cron jobs" > /etc/cron.d/tiktok_cron
echo "0 */4 * * * /usr/local/bin/python /app/main_four_tik_tok.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/tiktok_cron
echo "0 0 * * * /usr/local/bin/python /app/main_once_day_tik_tok.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/tiktok_cron

# Установка прав и обновление cron задач
chmod 0644 /etc/cron.d/tiktok_cron
crontab /etc/cron.d/tiktok_cron

# Проверка установленных заданий
echo "Установленные cron-задания:"
crontab -l

# Запуск cron демона в фоне
cron

# Создание необходимых директорий
mkdir -p data/temp data/user_info data/user_live_list data/user_live_analytics logs

# Инициализация настроек на основе переменных окружения
python3 -c "
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
API_BASE_URL = '{os.environ.get(\"API_BASE_URL\", \"http://api:5000/api\")}'
API_TIMEOUT = {os.environ.get(\"API_TIMEOUT\", \"30\")}
API_MAX_RETRIES = {os.environ.get(\"API_MAX_RETRIES\", \"10\")}
API_RETRY_DELAY = {os.environ.get(\"API_RETRY_DELAY\", \"5\")}

# Директории для данных
DATA_DIR = Path(\"./data\")
TEMP_DIR = DATA_DIR / \"temp\"
USER_INFO_DIR = DATA_DIR / \"user_info\"
USER_LIVE_LIST_DIR = DATA_DIR / \"user_live_list\"
USER_LIVE_ANALYTICS_DIR = DATA_DIR / \"user_live_analytics\"

# Путь к файлу с данными пользователями
USER_JSON_FILE = DATA_DIR / \"users.json\"

# Настройки логирования
LOG_LEVEL = '{os.environ.get(\"LOG_LEVEL\", \"INFO\")}'
LOG_FORMAT = \"%(asctime)s | %(levelname)s | %(lineno)d | %(message)s\"
'''

# Записываем в файл
with open(config_file, 'w') as f:
    f.write(config_content)

print(f'Конфигурация записана в {config_file}')
"


# Вывод информации о запуске
echo "============================================"
echo "TikTok API Client запущен в $(date)"
echo "Часовой пояс: ${TZ}"
echo "API: ${API_BASE_URL}"
echo "Cron задачи:"
echo "- Ежедневно: запуск main_once_day_tik_tok.py в 00:00 UTC"
echo "- Каждые 4 часа: запуск main_four_tik_tok.py в 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC"
echo "============================================"

# Запуск задач при старте контейнера (если нужно)
if [ "${RUN_ON_START}" = "true" ]; then
  echo "Запускаем задачи при старте контейнера..."
  python /app/main_once_day_tik_tok.py &
  python /app/main_four_tik_tok.py &
fi

# Чтобы контейнер не завершался
tail -f /var/log/cron.log