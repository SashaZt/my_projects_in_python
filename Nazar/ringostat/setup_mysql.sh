#!/bin/bash

# Скрипт для автоматической установки и настройки MySQL на Ubuntu
# Сделайте его исполняемым: chmod +x setup_mysql.sh
# Запустите скрипт: ./setup_mysql.sh

# 1. Проверка наличия MySQL
MYSQL_VERSION=$(mysql --version 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "MySQL уже установлен: $MYSQL_VERSION"
    read -p "Хотите продолжить установку и переустановить MySQL? (y/n): " choice
    case "$choice" in
        y|Y ) echo "Продолжаем установку...";;
        n|N ) echo "Установка отменена."; exit 0;;
        * ) echo "Неверный ввод. Установка отменена."; exit 1;;
    esac
fi

# 2. Обновление списка пакетов
echo "Обновляем список пакетов..."
sudo apt update

# 3. Установка обновлений
echo "Устанавливаем обновления системы..."
sudo apt upgrade -y

# 4. Установка MySQL Server
echo "Устанавливаем MySQL сервер..."
sudo apt install mysql-server -y

# 5. Запуск MySQL службы
echo "Запускаем MySQL сервер..."
sudo systemctl start mysql

# 6. Настройка безопасности MySQL с предопределёнными ответами
# Здесь мы используем echo для автоматизации взаимодействия с mysql_secure_installation
echo "Настраиваем MySQL с помощью mysql_secure_installation..."

sudo mysql_secure_installation <<EOF
n
Y
Y
Y
Y
EOF

# 7. Настройка MySQL для внешних подключений (правка bind-address)
echo "Настраиваем MySQL для внешних подключений (bind-address)..."
sudo sed -i "s/bind-address\s*=\s*127.0.0.1/bind-address = 0.0.0.0/" /etc/mysql/mysql.conf.d/mysqld.cnf

# 8. Настройка брандмауэра (открытие портов 3306 и 22)
echo "Настраиваем брандмауэр (открытие портов 3306 и 22)..."
sudo ufw allow 3306/tcp
sudo ufw allow 22/tcp

# 9. Включение UFW и подтверждение включения
echo "Включаем брандмауэр UFW..."
sudo ufw enable <<< "y"

# 10. Оптимизация конфигурации MySQL
echo "Оптимизируем конфигурацию MySQL для производительности..."

# Вносим изменения в /etc/mysql/my.cnf
sudo tee -a /etc/mysql/my.cnf > /dev/null <<EOT

[mysqld]
# Основные параметры
max_connections = 100
table_open_cache = 400
thread_cache_size = 10

# Память
tmp_table_size = 32M
max_heap_table_size = 32M

# InnoDB параметры
innodb_buffer_pool_size = 2G  # 50-70% от всей доступной ОЗУ
innodb_redo_log_capacity = 512M  # Замена устаревших innodb_log_file_size и innodb_log_files_in_group
innodb_log_buffer_size = 64M
innodb_flush_log_at_trx_commit = 1
innodb_lock_wait_timeout = 50

# Обработка запросов
key_buffer_size = 256M
sort_buffer_size = 4M
read_buffer_size = 2M
read_rnd_buffer_size = 4M
myisam_sort_buffer_size = 64M
EOT

# 11. Создание пользователя MySQL и предоставление прав
echo "Создаём пользователя 'python_mysql' с правами для всех баз данных..."

# Создание пользователя и предоставление привилегий
sudo mysql <<EOF
CREATE USER 'python_mysql'@'%' IDENTIFIED BY 'python_mysql';
GRANT ALL PRIVILEGES ON *.* TO 'python_mysql'@'%';
FLUSH PRIVILEGES;
EOF

# 12. Перезапуск службы MySQL для применения настроек
echo "Перезапускаем MySQL для применения новых настроек..."
sudo systemctl restart mysql

echo "Установка и настройка MySQL завершена!"
