#!/bin/bash

BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"
source ./.env

BACKUP_DATE=$(date +"%Y_%m_%d_%H_%M")
BACKUP_FILE="${BACKUP_DIR}/backup_${BACKUP_DATE}.backup"
CONTAINER_NAME="db"
DB_USER="${POSTGRES_USER}"
DB_NAME="${POSTGRES_DB}"

echo "Creating backup ${BACKUP_FILE}..."

# Внутренний путь в контейнере
TEMP_BACKUP_PATH="/tmp/db_backup_${BACKUP_DATE}.dump"

# Создание бэкапа внутри контейнера
docker exec $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME -F c -f "$TEMP_BACKUP_PATH"
if [ $? -ne 0 ]; then
  echo "Backup failed inside container."
  exit 1
fi

# Копирование бэкапа из контейнера
docker cp "$CONTAINER_NAME:$TEMP_BACKUP_PATH" "$BACKUP_FILE"
docker exec $CONTAINER_NAME rm "$TEMP_BACKUP_PATH"

echo "Backup created successfully: ${BACKUP_FILE}"

# Удаление старых бэкапов
cd "$BACKUP_DIR"
ls -t *.backup | tail -n +6 | xargs -r rm
echo "Old backups cleaned up."
