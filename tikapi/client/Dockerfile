FROM python:3.12-slim

# Устанавливаем рабочую директорию и необходимые пакеты
WORKDIR /app
RUN apt-get update && apt-get install -y openssl curl cron tzdata

# Установка часового пояса (замените Europe/Moscow на ваш часовой пояс)
ENV TZ=Europe/Kyiv
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Копируем файл зависимостей и устанавливаем библиотеки
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения
COPY . /app

# Создаем файл для журналов cron
RUN touch /var/log/cron.log

# Создаем файл с заданиями cron
RUN echo "0 */4 * * * /usr/local/bin/python /app/main_four_tik_tok.py >> /var/log/cron.log 2>&1" > /etc/cron.d/tiktok_cron
RUN echo "0 0 * * * /usr/local/bin/python /app/main_once_day_tik_tok.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/tiktok_cron

# Даем права на выполнение файлу cron
RUN chmod 0644 /etc/cron.d/tiktok_cron

# Активируем cron задачу
RUN crontab /etc/cron.d/tiktok_cron

# Создаем скрипт запуска
COPY startup.sh /startup.sh
RUN chmod +x /startup.sh

# Запускаем сервисы
CMD ["/startup.sh"]