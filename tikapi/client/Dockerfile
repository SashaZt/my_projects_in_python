FROM python:3.12-slim

# Установка рабочей директории
WORKDIR /app

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y openssl curl cron tzdata

# Установка часового пояса
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создание необходимых директорий
RUN mkdir -p data/temp data/user_info data/user_live_list data/user_live_analytics logs

# Копирование скрипта запуска и установка прав
COPY startup.sh /app/
RUN chmod +x /app/startup.sh

# Копирование остального исходного кода
COPY . /app

# Создание файла для логов cron
RUN touch /var/log/cron.log

# Обеспечение правильных прав доступа
RUN chmod +x /app/*.py
RUN chmod +x /app/startup.sh
RUN chmod 755 /app/startup.sh

# Важное изменение: используем bash для запуска скрипта, 
# а не прямое выполнение скрипта
CMD ["bash", "/app/startup.sh"]