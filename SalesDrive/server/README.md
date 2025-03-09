# PostgreSQL Import Project

Проект для импорта данных из JSON в PostgreSQL с использованием Python, SQLAlchemy и Alembic.

## Структура проекта

```
postgres_import_project/
├── alembic/                     # Папка с миграциями Alembic
│   ├── versions/                # Версии миграций
│   ├── env.py                   # Конфигурация среды Alembic
│   └── script.py.mako           # Шаблон для миграций
├── app/                         # Основной код приложения
│   ├── config.py                # Конфигурация приложения
│   ├── db/                      # Модуль для работы с базой данных
│   │   ├── base.py              # Базовые классы SQLAlchemy
│   │   ├── session.py           # Управление сессиями
│   │   └── engine.py            # Настройка движка БД
│   ├── models/                  # Модели данных SQLAlchemy
│   │   ├── contacts.py          # Модели контактов
│   │   ├── orders.py            # Модели заказов
│   │   ├── products.py          # Модели товаров
│   │   └── enums.py             # Справочники
│   ├── schemas/                 # Pydantic-схемы
│   │   └── json_schema.py       # Схемы для JSON-данных
│   └── services/                # Сервисы приложения
│       └── import_service.py    # Сервис импорта данных
├── main.py                      # Точка входа в приложение
├── alembic.ini                  # Конфигурация Alembic
├── .env                         # Переменные окружения
└── requirements.txt             # Зависимости Python
```

## Требования

- Python 3.9+
- PostgreSQL 12+

## Установка и настройка

1. Клонируйте репозиторий:

```bash
git clone <repo-url>
cd postgres_import_project
```

2. Создайте виртуальное окружение и установите зависимости:

```bash
python -m venv venv
source venv/bin/activate  # На Windows используйте venv\Scripts\activate
pip install -r requirements.txt
```

3. Настройте переменные окружения в файле `.env`.
4. Создайте базу данных в PostgreSQL:

```bash
createdb postgres_import  # Или создайте через pgAdmin/psql
```

5. Запустите миграции:

```bash
alembic upgrade head
```

## Использование

### Импорт данных из JSON-файла

```bash
python main.py /path/to/your/json/file.json
```

### Создание новой миграции

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Применение миграций

```bash
alembic upgrade head  # Применить все миграции
alembic upgrade +1    # Применить следующую миграцию
alembic downgrade -1  # Откатить последнюю миграцию
```

## Лицензия

MIT
