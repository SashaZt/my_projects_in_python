#!/bin/bash

# Цветной вывод для удобства
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Создание структуры папок и пустых файлов для проекта...${NC}"

# Создание основной директории проекта
mkdir -p telegram_payment_bot
cd telegram_payment_bot

# Создание пустых файлов в корне проекта
touch .env
touch .gitignore
touch docker-compose.yml

# Структура для PostgreSQL
mkdir -p db/init
touch db/Dockerfile
touch db/init/01-init.sql

# Структура для бота
mkdir -p bot/{handlers,keyboards,middlewares,utils,db}
touch bot/Dockerfile
touch bot/requirements.txt
touch bot/main.py
touch bot/config.py

# Создание пустых файлов инициализации в каждой папке
touch bot/{handlers,keyboards,middlewares,utils,db}/__init__.py

# Создание пустых файлов в папках бота
touch bot/handlers/{start.py,menu.py,buy.py,support.py,user_purchases.py}
touch bot/keyboards/{reply.py,inline.py}
touch bot/middlewares/throttling.py
touch bot/utils/{states.py,notifications.py}
touch bot/db/{database.py,models.py}

# Структура для платежного сервиса
mkdir -p payment_service/{api,processors,db}
touch payment_service/Dockerfile
touch payment_service/requirements.txt
touch payment_service/main.py
touch payment_service/config.py

# Создание пустых файлов инициализации в каждой папке
touch payment_service/{api,processors,db}/__init__.py

# Создание пустых файлов в папках платежного сервиса
touch payment_service/api/{portmone.py,webhook.py}
touch payment_service/processors/{payment.py,card.py}
touch payment_service/db/{database.py,models.py}

echo -e "${GREEN}Структура проекта успешно создана!${NC}"
echo -e "${BLUE}Теперь вы можете начать разработку, заполняя созданные файлы.${NC}"