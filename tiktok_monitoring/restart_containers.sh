# Путь к директории проекта
PROJECT_DIR=/root/tiktok_monitoring

# Переходим в директорию проекта
cd $PROJECT_DIR

# Логируем начало перезапуска
echo "$(date) - Начало перезапуска контейнеров" >> restart_log.txt

# Останавливаем все контейнеры
docker-compose down

# Небольшая пауза
sleep 5

# Запускаем контейнеры заново
./start.sh

# Логируем результат
echo "$(date) - Контейнеры перезапущены" >> restart_log.txt

# Проверяем статус и логируем
docker-compose ps >> restart_log.txt
echo "-------------------------------" >> restart_log.txt
</parameter>
antml:invoke>
antml:function_calls

# Этот скрипт:
# 1. Переходит в директорию вашего проекта
# 2. Останавливает все контейнеры
# 3. Запускает их снова с помощью вашего start.sh
# 4. Логирует действия в файл restart_log.txt

# 2. Затем сделайте скрипт исполняемым:

# ```bash
# chmod +x restart_containers.sh