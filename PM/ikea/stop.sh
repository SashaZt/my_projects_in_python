#!/bin/bash

# Цветовое оформление
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Остановка системы...${NC}"

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

# Проверяем что docker-compose.yml существует
if [ ! -f "docker-compose.yml" ] && [ ! -f "docker-compose.yaml" ]; then
    echo -e "${RED}Файл docker-compose.yml не найден!${NC}"
    exit 1
fi

# Показываем статус контейнеров перед остановкой
echo -e "${BLUE}Текущий статус контейнеров:${NC}"
$DOCKER_COMPOSE ps

# Остановка и удаление контейнеров
echo -e "${YELLOW}Остановка контейнеров...${NC}"
$DOCKER_COMPOSE down

# Показываем финальный статус
echo -e "${BLUE}Проверка остановки:${NC}"
$DOCKER_COMPOSE ps

echo -e "${GREEN}Система остановлена!${NC}"

# # Подсказки для дополнительной очистки
# echo ""
# echo -e "${YELLOW}Дополнительные команды для очистки:${NC}"
# echo -e "  ${BLUE}Удалить volumes:${NC} $DOCKER_COMPOSE down -v"
# echo -e "  ${BLUE}Очистить образы:${NC} docker image prune -f"
# echo -e "  ${BLUE}Полная очистка:${NC} docker system prune -af --volumes"