#!/bin/bash
# Файл: alembic_migrate.sh

# Проверка наличия конфигурации
if [ ! -f "config.json" ]; then
    echo "Ошибка: файл config.json не найден!"
    exit 1
fi

# Функция вывода справки
show_help() {
    echo "Скрипт для управления миграциями базы данных с помощью Alembic"
    echo ""
    echo "Использование: ./migrate.sh [команда]"
    echo ""
    echo "Команды:"
    echo "  create [название]  - Создать новую миграцию (например, ./migrate.sh create add_users_table)"
    echo "  upgrade [ревизия]  - Применить миграции, по умолчанию до последней (head)"
    echo "  downgrade [ревизия] - Откатить миграции до указанной ревизии"
    echo "  history           - Показать историю миграций"
    echo "  current           - Показать текущую ревизию"
    echo "  help              - Показать эту справку"
    echo ""
}

# Проверка наличия директории alembic
if [ ! -d "alembic" ]; then
    echo "Директория alembic не найдена. Инициализируем Alembic..."
    alembic init alembic
    
    # Модифицируем env.py (примечание: это упрощенная версия, полную замену лучше делать вручную)
    echo "Обратите внимание: вам может потребоваться вручную настроить файл alembic/env.py"
    echo "См. документацию проекта для более подробной информации."
fi

# Обработка команд
case "$1" in
    create)
        if [ -z "$2" ]; then
            echo "Ошибка: необходимо указать название миграции"
            show_help
            exit 1
        fi
        alembic revision --autogenerate -m "$2"
        ;;
    upgrade)
        alembic upgrade ${2:-head}
        ;;
    downgrade)
        if [ -z "$2" ]; then
            echo "Ошибка: необходимо указать ревизию для отката"
            show_help
            exit 1
        fi
        alembic downgrade $2
        ;;
    history)
        alembic history
        ;;
    current)
        alembic current
        ;;
    help|*)
        show_help
        ;;
esac