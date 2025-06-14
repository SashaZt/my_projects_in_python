#!/bin/bash

# Цветовое оформление
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Подготовка конфигурации для запуска системы...${NC}"

# Проверка наличия config.json
if [ ! -f "config.json" ]; then
    echo -e "${RED}❌ Файл config.json не найден!${NC}"
    exit 1
fi

# Проверка наличия config_loader.py
if [ ! -f "config_loader.py" ]; then
    echo -e "${RED}❌ Файл config_loader.py не найден!${NC}"
    exit 1
fi

# Показываем доступные компоненты
echo -e "${CYAN}📋 Анализ конфигурации...${NC}"
python3 config_loader.py show

echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"

# Генерация всех конфигураций
echo -e "${BLUE}🔄 Генерация всех конфигураций...${NC}"
python3 config_loader.py generate-all

# Проверяем результат генерации
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ошибка при генерации конфигураций!${NC}"
    exit 1
fi

echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"

# Показываем сгенерированные файлы
echo -e "${YELLOW}📁 Сгенерированные файлы конфигурации:${NC}"


# Файлы в директориях сервисов
for dir in */; do
    dir_name=$(basename "$dir")
    if [ -f "$dir/.env" ]; then
        env_count=$(grep -c '^[^#]' "$dir/.env" 2>/dev/null || echo "0")
        echo -e "${GREEN}   ✅ $dir/.env${NC} (локальная конфигурация, $env_count переменных)"
    fi
    if [ -f "$dir${dir_name}_config.json" ]; then
        echo -e "${GREEN}   ✅ $dir${dir_name}_config.json${NC} (JSON конфигурация)"
    fi
done

echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"

# Проверка доступной команды Docker Compose
echo -e "${BLUE}🐳 Проверка версии Docker Compose...${NC}"
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    docker_version=$(docker compose version --short 2>/dev/null || docker compose version | head -1)
    echo -e "${BLUE}   ✅ Используется: docker compose ($docker_version)${NC}"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    docker_version=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
    echo -e "${BLUE}   ✅ Используется: docker-compose ($docker_version)${NC}"
else
    echo -e "${RED}❌ Ни docker compose, ни docker-compose не найдены! Установите Docker Compose.${NC}"
    exit 1
fi
# Проверка наличия docker-compose.yml
compose_file="docker-compose.yml"


# Проверка и запуск Docker Compose
if [ -n "$compose_file" ]; then
    echo -e "${GREEN}🚀 Запуск системы...${NC}"
    $DOCKER_COMPOSE -f "$compose_file" up -d --build

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Система успешно запущена!${NC}"
        echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"
        echo -e "${BLUE}📊 Статус контейнеров:${NC}"
        $DOCKER_COMPOSE -f "$compose_file" ps
        
        echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"
        echo -e "${CYAN}🔗 Полезные команды:${NC}"
        echo -e "${YELLOW}   Просмотр логов:${NC}     $DOCKER_COMPOSE logs -f"
        echo -e "${YELLOW}   Остановка:${NC}         $DOCKER_COMPOSE down"
        echo -e "${YELLOW}   Перезапуск:${NC}        $DOCKER_COMPOSE restart"
        echo -e "${YELLOW}   Статус:${NC}            $DOCKER_COMPOSE ps"
        
        # Показываем информацию о сервисах
        echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"
        echo -e "${CYAN}📋 Информация о сервисах:${NC}"
        
        if [ -f ".env" ]; then
            PROJECT_NAME=$(grep "^PROJECT_NAME=" .env | cut -d'=' -f2 | tr -d '"')
            POSTGRES_PORT=$(grep "^POSTGRES_PORT=" .env | cut -d'=' -f2 | tr -d '"')
            
            if [ -n "$PROJECT_NAME" ]; then
                echo -e "${GREEN}   🗄️  База данных:${NC}    ${PROJECT_NAME}_db"
                if [ -n "$POSTGRES_PORT" ]; then
                    echo -e "${GREEN}   🔌 PostgreSQL:${NC}     localhost:${POSTGRES_PORT}"
                fi
                echo -e "${GREEN}   🔧 Client:${NC}         ${PROJECT_NAME}_client"
            fi
        fi
    else
        echo -e "${RED}❌ Ошибка при запуске системы!${NC}"
        echo -e "${YELLOW}📋 Проверьте логи:${NC} $DOCKER_COMPOSE logs"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Docker Compose файл не найден или не создан${NC}"
    exit 1
fi

echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 Готово! Система запущена и готова к работе!${NC}"