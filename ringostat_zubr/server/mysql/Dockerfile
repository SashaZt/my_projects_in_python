# Используем официальный образ MySQL
FROM mysql:8.0

# Устанавливаем переменные окружения для автоматической установки
ENV MYSQL_ROOT_PASSWORD=example
ENV MYSQL_DATABASE=my_database
ENV MYSQL_USER=python_mysql
ENV MYSQL_PASSWORD=python_mysql

# Копируем скрипт для настройки MySQL
COPY mysql_secure_installation.sql /docker-entrypoint-initdb.d/
COPY my.cnf /etc/mysql/my.cnf

# Настраиваем MySQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    ufw && \
    echo "Настраиваем MySQL с помощью mysql_secure_installation..." && \
    echo "n\nY\nY\nY\nY" | mysql_secure_installation && \
    echo "Настраиваем MySQL для внешних подключений..." && \
    sed -i "s/bind-address\s*=\s*127.0.0.1/bind-address = 0.0.0.0/" /etc/mysql/mysql.conf.d/mysqld.cnf && \
    echo "Настраиваем брандмауэр..." && \
    ufw allow 3306/tcp && \
    ufw allow 22/tcp && \
    ufw enable && \
    echo "Настройка завершена."

# Перезапускаем MySQL для применения новых настроек
CMD ["mysqld"]
