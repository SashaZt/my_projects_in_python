#!/bin/bash

# Проверка наличия аргумента
if [ $# -eq 0 ]; then
  echo "Error: Backup filename is required."
  echo "Usage: $0 backup_filename.backup"
  exit 1
fi

# Директория с бекапами
BACKUP_DIR="./backups"
BACKUP_FILE="${BACKUP_DIR}/$1"

# Проверка существования файла
if [ ! -f "$BACKUP_FILE" ]; then
  echo "Error: Backup file not found: $BACKUP_FILE"
  echo "Available backups:"
  ls -lt ${BACKUP_DIR}/*.backup 2>/dev/null || echo "No backups found in $BACKUP_DIR"
  exit 1
fi

# Загрузка переменных окружения
source ./.env

# Имя контейнера
CONTAINER_NAME="${PROJECT_NAME}_db"


# Данные для подключения
DB_USER="${POSTGRES_USER}"
DB_NAME="${POSTGRES_DB}"

echo "Restoring database from backup: $BACKUP_FILE"
echo "WARNING: This will overwrite the current database. Press Ctrl+C to cancel."
echo "Continuing in 5 seconds..."
sleep 5

# Восстановление из бекапа
echo "Starting restoration..."
cat $BACKUP_FILE | docker exec -i $CONTAINER_NAME pg_restore -U $DB_USER -d $DB_NAME --clean --if-exists

# Проверка успешности выполнения
if [ $? -eq 0 ]; then
  echo "Database restored successfully from $BACKUP_FILE"
else
  echo "Restoration from $BACKUP_FILE failed!"
  exit 1
fi