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

# Генерация config.py
echo -e "${BLUE}🔄 Генерация config.py...${NC}"
python3 generate_config.py 

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

# # Проверка доступной команды Docker Compose
# echo -e "${BLUE}🐳 Проверка версии Docker Compose...${NC}"
# if command -v docker &> /dev/null && docker compose version &> /dev/null; then
#     DOCKER_COMPOSE="docker compose"
#     docker_version=$(docker compose version --short 2>/dev/null || docker compose version | head -1)
#     echo -e "${BLUE}   ✅ Используется: docker compose ($docker_version)${NC}"
# elif command -v docker-compose &> /dev/null; then
#     DOCKER_COMPOSE="docker-compose"
#     docker_version=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
#     echo -e "${BLUE}   ✅ Используется: docker-compose ($docker_version)${NC}"
# else
#     echo -e "${RED}❌ Ни docker compose, ни docker-compose не найдены! Установите Docker Compose.${NC}"
#     exit 1
# fi
echo -e "${CYAN}🔄 Запуск клиента...${NC}"
if [ -f "/app/start_client.sh" ]; then
    chmod +x /app/start_client.sh
    bash /app/start_client.sh
    client_exit_code=$?  # Добавьте эту строку!
else
    echo -e "${RED}❌ Файл start_client.sh не найден!${NC}"
    exit 1
fi
# # Проверка наличия docker-compose.yml
# compose_file="docker-compose.yml"

# # Проверка и запуск Docker Compose
# if [ -f "$compose_file" ]; then
#     echo -e "${GREEN}🏗️  Этап 1: Запуск базы данных...${NC}"
    
#     # Сначала запускаем только базу данных
#     $DOCKER_COMPOSE -f "$compose_file" up -d --build db

#     if [ $? -ne 0 ]; then
#         echo -e "${RED}❌ Ошибка при запуске базы данных!${NC}"
#         exit 1
#     fi

#     # Ждем готовности базы данных
#     echo -e "${YELLOW}⏳ Ожидание готовности базы данных...${NC}"
#     timeout=120
#     counter=0
#     while [ $counter -lt $timeout ]; do
#         if $DOCKER_COMPOSE -f "$compose_file" exec -T db pg_isready -U ${POSTGRES_USER:-postgres} >/dev/null 2>&1; then
#             echo -e "${GREEN}✅ База данных готова!${NC}"
#             break
#         fi
#         sleep 3
#         counter=$((counter + 3))
#         printf "."
#     done
#     echo ""
    
#     if [ $counter -ge $timeout ]; then
#         echo -e "${RED}❌ Превышено время ожидания готовности БД${NC}"
#         echo -e "${YELLOW}📋 Логи базы данных:${NC}"
#         $DOCKER_COMPOSE -f "$compose_file" logs db
#         exit 1
#     fi

#     echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"
#     echo -e "${GREEN}🌐 Этап 2: Запуск веб-сервиса...${NC}"
    
#     # Запускаем веб-сервис
#     $DOCKER_COMPOSE -f "$compose_file" up -d --build web

#     if [ $? -ne 0 ]; then
#         echo -e "${RED}❌ Ошибка при запуске веб-сервиса!${NC}"
#         exit 1
#     fi

#     # Ждем готовности веб-сервиса
#     echo -e "${YELLOW}⏳ Ожидание готовности веб-сервиса...${NC}"
#     sleep 5
    
#     # Проверяем статус веб-сервиса
#     if $DOCKER_COMPOSE -f "$compose_file" ps web | grep -q "Up"; then
#         echo -e "${GREEN}✅ Веб-сервис готов!${NC}"
#     else
#         echo -e "${YELLOW}⚠️  Веб-сервис запущен, но проверим логи...${NC}"
#         $DOCKER_COMPOSE -f "$compose_file" logs --tail=10 web
#     fi

#     echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"
#     echo -e "${BLUE}📊 Статус основных сервисов:${NC}"
#     $DOCKER_COMPOSE -f "$compose_file" ps

#     echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"
#     echo -e "${BLUE}🎯 Этап 3: Запуск клиента (одноразовый с автоудалением)...${NC}"
    
#     # Даем дополнительное время для стабилизации системы
#     echo -e "${YELLOW}⏳ Ожидание стабилизации системы (3 сек)...${NC}"
#     sleep 3
    
#     # # Запускаем client с автоудалением
#     # echo -e "${CYAN}🔄 Запуск клиента...${NC}"
#     # $DOCKER_COMPOSE -f "$compose_file" run --rm --build client
    
#     # client_exit_code=$?
#     # Запускаем client напрямую через start_client.sh вместо Docker Compose
#     echo -e "${CYAN}🔄 Запуск клиента...${NC}"
#     if [ -f "/app/start_client.sh" ]; then
#         chmod +x /app/start_client.sh
#         bash /app/start_client.sh
#         client_exit_code=$?  # Добавьте эту строку!
#     else
#         echo -e "${RED}❌ Файл start_client.sh не найден!${NC}"
#         exit 1
#     fi
#     echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"
    
#     if [ $client_exit_code -eq 0 ]; then
#         echo -e "${GREEN}✅ Клиент успешно выполнил задачу и был удален!${NC}"
#     else
#         echo -e "${YELLOW}⚠️  Клиент завершился с кодом $client_exit_code${NC}"
#         echo -e "${CYAN}📋 Последние логи клиента можно увидеть выше${NC}"
#     fi
    
#     echo -e "${BLUE}📊 Статус оставшихся контейнеров:${NC}"
#     $DOCKER_COMPOSE -f "$compose_file" ps
    
#     echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"
#     echo -e "${CYAN}🔗 Полезные команды:${NC}"
#     echo -e "${YELLOW}   Просмотр логов:${NC}      $DOCKER_COMPOSE logs -f"
#     echo -e "${YELLOW}   Логи конкретного сервиса:${NC} $DOCKER_COMPOSE logs -f [db|web]"
#     echo -e "${YELLOW}   Остановка:${NC}          $DOCKER_COMPOSE down"
#     echo -e "${YELLOW}   Перезапуск:${NC}         $DOCKER_COMPOSE restart"
#     echo -e "${YELLOW}   Статус:${NC}             $DOCKER_COMPOSE ps"
#     echo -e "${YELLOW}   Повторный запуск client:${NC} $DOCKER_COMPOSE run --rm client"
    
#     # Показываем информацию о сервисах
#     echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"
#     echo -e "${CYAN}📋 Информация о сервисах:${NC}"
    
#     if [ -f ".env" ]; then
#         PROJECT_NAME=$(grep "^PROJECT_NAME=" .env | cut -d'=' -f2 | tr -d '"')
#         POSTGRES_PORT=$(grep "^POSTGRES_PORT=" .env | cut -d'=' -f2 | tr -d '"')
        
#         if [ -n "$PROJECT_NAME" ]; then
#             echo -e "${GREEN}   🗄️  База данных:${NC}    ${PROJECT_NAME}_db (постоянный)"
#             if [ -n "$POSTGRES_PORT" ]; then
#                 echo -e "${GREEN}   🔌 PostgreSQL:${NC}     localhost:${POSTGRES_PORT}"
#             fi
#             echo -e "${GREEN}   🌐 Web сервис:${NC}     localhost:8000 (постоянный)"
#             echo -e "${CYAN}   🎯 Client:${NC}         выполнен и удален"
#         fi
#     fi
    
# else
#     echo -e "${YELLOW}⚠️  Docker Compose файл не найден или не создан${NC}"
#     exit 1
# fi

# echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"
# echo -e "${GREEN}🎉 Готово! Система запущена в правильном порядке!${NC}"
# echo -e "${CYAN}💡 Порядок: DB → WEB → CLIENT (удален)${NC}"
# echo -e "${GREEN}📍 Основные сервисы (db, web) продолжают работать${NC}"