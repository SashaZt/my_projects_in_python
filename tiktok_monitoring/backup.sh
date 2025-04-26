#!/bin/bash

# Директория для хранения бекапов
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR
source ./.env
# Формат имени файла бекапа
BACKUP_DATE=$(date +"%Y_%m_%d_%H_%M")
BACKUP_FILE="${BACKUP_DIR}/backup_${BACKUP_DATE}.backup"

# Имя контейнера
CONTAINER_NAME="tiktok_monitoring-postgres"

# Данные для подключения
DB_USER="${POSTGRES_USER}"
DB_NAME="${POSTGRES_DB}"

echo "Creating backup ${BACKUP_FILE}..."
docker exec -t $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME -F c > $BACKUP_FILE

# Проверка успешности выполнения
if [ $? -eq 0 ]; then
  echo "Backup created successfully: ${BACKUP_FILE}"
else
  echo "Backup failed!"
  exit 1
fi

# Опционально: удаление старых бекапов (оставляем только последние 5)
cd $BACKUP_DIR
ls -t *.backup | tail -n +6 | xargs -r rm
echo "Old backups cleaned up."