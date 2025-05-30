#!/bin/bash

# Цветовое оформление
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Подготовка конфигурации для запуска...${NC}"

# Проверка наличия config.json
if [ ! -f "config.json" ]; then
    echo -e "${RED}Файл config.json не найден!${NC}"
    exit 1
fi

# Проверка наличия config_loader.py
if [ ! -f "config_loader.py" ]; then
    echo -e "${RED}Файл config_loader.py не найден!${NC}"
    exit 1
fi

# Генерация основного .env файла
echo -e "${BLUE}Генерация основного .env файла...${NC}"
python3 config_loader.py

# Генерация компонент-специфичных конфигураций
echo -e "${BLUE}Генерация конфигурации для бота...${NC}"
python3 -c "from config_loader import generate_component_config; generate_component_config(component='bot', output_format='env')"

echo -e "${BLUE}Генерация конфигурации для платежного сервиса...${NC}"
python3 -c "from config_loader import generate_component_config; generate_component_config(component='payment_service', output_format='env')"

echo -e "${BLUE}Генерация конфигурации для базы данных...${NC}"
python3 -c "from config_loader import generate_component_config; generate_component_config(component='db', output_format='env')"

# Запуск docker-compose
echo -e "${GREEN}Запуск системы...${NC}"
docker-compose up -d --build

echo -e "${GREEN}Система запущена!${NC}"