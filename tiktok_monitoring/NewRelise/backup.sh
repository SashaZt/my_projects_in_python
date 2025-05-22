#!/bin/bash

# Директория для хранения бекапов
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR
source ./.env

# Формат имени файла бекапа
BACKUP_DATE=$(date +"%Y_%m_%d_%H_%M")
FULL_BACKUP_FILE="${BACKUP_DIR}/backup_${BACKUP_DATE}.backup"
SCHEMA_BACKUP_FILE="${BACKUP_DIR}/schema_${BACKUP_DATE}.sql"

# Имя контейнера
CONTAINER_NAME="tiktok_monitoring-postgres"

# Данные для подключения
DB_USER="${POSTGRES_USER}"
DB_NAME="${POSTGRES_DB}"

# Функция для очистки старых бекапов
cleanup_old_backups() {
  echo "Cleaning up old backups..."
  cd $BACKUP_DIR
  # Очистка полных бекапов (оставляем 5 последних)
  ls -t *.backup 2>/dev/null | tail -n +6 | xargs -r rm
  # Очистка бекапов схемы (оставляем 5 последних)
  ls -t schema_*.sql 2>/dev/null | tail -n +6 | xargs -r rm
  echo "Old backups cleaned up."
}

# Вывод меню выбора
echo "===== TikTok Мониторинг - Утилита резервного копирования ====="
echo "Выберите тип бекапа:"
echo "1) Полный бекап базы данных"
echo "2) Бекап только схемы, функций и триггеров"
echo "3) Выход"
echo ""
read -p "Введите номер опции (1-3): " choice

case $choice in
  1)
    echo "Создание полного бекапа ${FULL_BACKUP_FILE}..."
    docker exec -t $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME -F c > $FULL_BACKUP_FILE
    
    # Проверка успешности выполнения
    if [ $? -eq 0 ]; then
      echo "Полный бекап успешно создан: ${FULL_BACKUP_FILE}"
      cleanup_old_backups
    else
      echo "Ошибка при создании бекапа!"
      exit 1
    fi
    ;;
    
  2)
    echo "Создание бекапа схемы ${SCHEMA_BACKUP_FILE}..."
    docker exec -t $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME --schema-only > $SCHEMA_BACKUP_FILE
    
    # Проверка успешности выполнения
    if [ $? -eq 0 ]; then
      echo "Бекап схемы успешно создан: ${SCHEMA_BACKUP_FILE}"
      cleanup_old_backups
    else
      echo "Ошибка при создании бекапа схемы!"
      exit 1
    fi
    ;;
    
  3)
    echo "Выход из программы."
    exit 0
    ;;
    
  *)
    echo "Некорректный выбор. Пожалуйста, введите число от 1 до 3."
    exit 1
    ;;
esac

echo "Операция завершена."