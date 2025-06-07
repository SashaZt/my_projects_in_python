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
python3 -c "from config_loader import generate_component_config; generate_component_config(component='client', output_format='env')"

# Проверка доступной команды Docker Compose
echo -e "${BLUE}Проверка версии Docker Compose...${NC}"
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    echo -e "${BLUE}Используется: docker compose ($(docker compose version))${NC}"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    echo -e "${BLUE}Используется: docker-compose ($(docker-compose --version))${NC}"
else
    echo -e "${RED}Ни docker compose, ни docker-compose не найдены! Установите Docker Compose.${NC}"
    exit 1
fi

# Запуск docker-compose
echo -e "${GREEN}Запуск системы...${NC}"
$DOCKER_COMPOSE up -d --build

echo -e "${GREEN}Система запущена!${NC}"