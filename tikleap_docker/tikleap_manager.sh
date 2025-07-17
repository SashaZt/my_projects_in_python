#!/bin/bash

# =============================================================================
# 🎯 TikLeap Authentication & Data Collection Manager
# Объединенный скрипт для управления Docker авторизацией + сбором данных
# =============================================================================

set -e  # Выход при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Переменные
CONTAINER_NAME="nodriver-manual-auth"
VNC_URL="http://localhost:6080"
VNC_PASSWORD="secret"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COOKIES_DIR="${SCRIPT_DIR}/cookies"
APP_DIR="${SCRIPT_DIR}/app"
CLIENT_DIR="${SCRIPT_DIR}/client"

# Функции для вывода
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Проверка зависимостей
check_dependencies() {
    log_step "Проверка зависимостей..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен!"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен!"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 не установлен!"
        exit 1
    fi
    
    log_success "Все зависимости установлены"
}

# Создание структуры папок
create_structure() {
    log_step "Создание структуры директорий..."
    
    mkdir -p "${APP_DIR}" "${COOKIES_DIR}" "${SCRIPT_DIR}/data" "${CLIENT_DIR}"
    
    log_success "Структура создана: ${SCRIPT_DIR}"
}

create_docker_compose() {
    log_step "Создание docker-compose.yml..."
    
    cat > "${SCRIPT_DIR}/docker-compose.yml" << 'EOF'
services:
  nodriver-auth:
    image: dorowu/ubuntu-desktop-lxde-vnc:latest
    container_name: nodriver-manual-auth
    ports:
      - "6080:80"
      - "5900:5900"
    volumes:
      - ./app:/workspace/app
      - ./cookies:/home/ubuntu/tikleap_work/cookies
      - ./data:/workspace/data
    environment:
      - VNC_PASSWORD=secret
      - RESOLUTION=1366x768
    
    mem_limit: 1g
    cpus: '1.0'
    shm_size: 512mb
    restart: "no"
    
    cap_add:
      - SYS_ADMIN
    security_opt:
      - seccomp:unconfined
EOF
    
    log_success "docker-compose.yml создан"
}

install_chrome_in_container() {
    log_step "Установка Chrome и Python зависимостей в контейнер..."
    
    # Ждем, пока контейнер полностью запустится
    sleep 10
    
    log_info "Обновление системы..."
    docker exec "${CONTAINER_NAME}" bash -c "apt-get update"
    
    log_info "Установка базовых пакетов..."
    docker exec "${CONTAINER_NAME}" bash -c "apt-get install -y python3 python3-pip wget curl gnupg"
    
    log_info "Добавление ключа Google Chrome (исправленный способ)..."
    docker exec "${CONTAINER_NAME}" bash -c "
        wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /etc/apt/trusted.gpg.d/google.gpg &&
        echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google-chrome.list
    "
    
    log_info "Обновление списка пакетов..."
    docker exec "${CONTAINER_NAME}" bash -c "apt-get update"
    
    log_info "Установка Google Chrome..."
    docker exec "${CONTAINER_NAME}" bash -c "apt-get install -y google-chrome-stable"
    
    log_info "Установка Python зависимостей..."
    docker exec "${CONTAINER_NAME}" bash -c "pip3 install nodriver loguru"
    
    log_info "Создание директорий..."
    docker exec "${CONTAINER_NAME}" bash -c "
        mkdir -p /home/ubuntu/tikleap_work/cookies &&
        chmod 777 /home/ubuntu/tikleap_work/cookies
    "
    
    log_success "Все зависимости установлены"
}
# Проверка статуса контейнера
check_container_status() {
    if docker ps -a --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        if docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
            echo "running"
        else
            echo "stopped"
        fi
    else
        echo "not_exists"
    fi
}

# Запуск контейнера
start_container() {
    log_step "Запуск Docker контейнера..."
    
    local status=$(check_container_status)
    
    case $status in
        "running")
            log_success "Контейнер уже запущен"
            ;;
        "stopped")
            log_info "Запуск остановленного контейнера..."
            docker-compose up -d
            ;;
        "not_exists")
            log_info "Создание и запуск нового контейнера..."
            docker-compose up -d
            ;;
    esac
    
    # Ожидание готовности
    log_info "Ожидание готовности контейнера..."
    for i in {1..30}; do
        if docker exec "${CONTAINER_NAME}" pgrep -f "chrome" > /dev/null 2>&1; then
            log_success "Контейнер готов к работе"
            return 0
        fi
        sleep 2
        echo -n "."
    done
    
    log_error "Контейнер не готов к работе"
    return 1
}

# Остановка контейнера
stop_container() {
    log_step "Остановка контейнера..."
    
    docker-compose down
    log_success "Контейнер остановлен"
}

# Установка зависимостей в контейнер
install_dependencies() {
    log_step "Установка Python зависимостей в контейнер..."
    
    # Проверяем, установлены ли уже зависимости
    if docker exec "${CONTAINER_NAME}" python3 -c "import nodriver" 2>/dev/null; then
        log_success "Зависимости уже установлены"
        return 0
    fi
    
    log_info "Установка nodriver и loguru..."
    docker exec "${CONTAINER_NAME}" bash -c "
        apt-get update > /dev/null 2>&1 && 
        apt-get install -y python3-pip > /dev/null 2>&1 &&
        pip3 install nodriver loguru pathlib > /dev/null 2>&1
    "
    
    log_success "Зависимости установлены"
}

# Копирование скрипта авторизации
copy_auth_script() {
    log_step "Копирование скрипта авторизации..."
    
    if [ ! -f "${APP_DIR}/auth_gui.py" ]; then
        log_error "Файл auth_gui.py не найден в ${APP_DIR}/"
        log_info "Поместите файл auth_gui.py в папку app/"
        return 1
    fi
    
    docker cp "${APP_DIR}/auth_gui.py" "${CONTAINER_NAME}:/workspace/app/"
    log_success "Скрипт скопирован в контейнер"
}

# Проверка и установка зависимостей для сбора данных
check_data_collection_deps() {
    log_step "Проверка зависимостей для сбора данных..."
    
    if [ ! -f "${CLIENT_DIR}/requirements.txt" ]; then
        log_error "Файл requirements.txt не найден в ${CLIENT_DIR}/"
        return 1
    fi
    
    if [ ! -f "${CLIENT_DIR}/main.py" ]; then
        log_error "Файл main.py не найден в ${CLIENT_DIR}/"
        return 1
    fi
    
    # Проверяем виртуальное окружение
    if [ ! -d "venv" ]; then
        log_info "Создание виртуального окружения..."
        python3 -m venv venv
    fi
    
    # Активируем виртуальное окружение и устанавливаем зависимости
    log_info "Установка зависимостей для сбора данных..."
    source venv/bin/activate
    
    # Проверяем нужно ли устанавливать зависимости
    if ! python3 -c "import gspread, rnet, loguru" &>/dev/null; then
        log_info "Установка недостающих зависимостей..."
        pip install -r "${CLIENT_DIR}/requirements.txt"
    else
        log_success "Все зависимости уже установлены"
    fi
    
    deactivate
    log_success "Зависимости для сбора данных готовы"
}

# Запуск сбора данных
run_data_collection() {
    log_step "Запуск сбора данных..."
    
    # Проверяем наличие cookies
    if [ ! -f "${COOKIES_DIR}/cookies_important.json" ]; then
        log_error "Cookies не найдены! Сначала выполните авторизацию."
        return 1
    fi
    
    # Проверяем зависимости
    if ! check_data_collection_deps; then
        log_error "Ошибка проверки зависимостей"
        return 1
    fi
    
    log_info "Запуск скрипта сбора данных..."
    
    # Переходим в директорию client и запускаем в виртуальном окружении
    cd "${CLIENT_DIR}"
    
    # Активируем venv и запускаем
    if source "${SCRIPT_DIR}/venv/bin/activate" && python3 main.py; then
        log_success "✅ Сбор данных завершен успешно"
        deactivate
        cd "${SCRIPT_DIR}"
        return 0
    else
        log_error "❌ Ошибка при сборе данных"
        deactivate
        cd "${SCRIPT_DIR}"
        return 1
    fi
}

# Полная автоматическая настройка и установка
auto_setup_and_install() {
    log_step "🤖 Полная автоматическая настройка..."
    
    # Отключаем set -e временно для этой функции
    set +e
    
    # 1. Проверка зависимостей
    check_dependencies
    
    # 2. Создание структуры
    create_structure
    create_docker_compose
    
    # 3. Запуск контейнера
    log_info "Запуск Docker контейнера..."
    docker-compose up -d
    
    # 3.5. Исправление прав доступа
    fix_permissions
    
    # 4. Ожидание готовности контейнера
    log_info "Ожидание готовности контейнера (до 60 секунд)..."
    for i in {1..30}; do
        if docker exec "${CONTAINER_NAME}" echo "ready" > /dev/null 2>&1; then
            log_success "Контейнер готов к настройке"
            break
        fi
        sleep 2
        echo -n "."
    done
    echo ""
    
    # 5. Установка зависимостей с правами root
    log_step "Установка всех зависимостей в контейнер..."
    
    # Детальная установка с правами root
    log_info "🔄 Обновление системных пакетов..."
    # if docker exec --user root "${CONTAINER_NAME}" bash -c "apt-get update"; then
    #     log_success "Пакеты обновлены"
    # else
    #     log_error "Ошибка обновления пакетов"
    #     set -e
    #     return 1
    # fi
    # install_chrome_in_container
    # log_info "📦 Установка системных зависимостей..."
    # if docker exec --user root "${CONTAINER_NAME}" bash -c "apt-get install -y python3-pip wget curl"; then
    #     log_success "Системные пакеты установлены"
    # else
    #     log_error "Ошибка установки системных пакетов"
    #     set -e
    #     return 1
    # fi
    
    # log_info "🐍 Проверка Python и pip..."
    # docker exec "${CONTAINER_NAME}" python3 --version
    # docker exec "${CONTAINER_NAME}" pip3 --version
    
    # log_info "📚 Установка Python зависимостей..."
    # # Сначала обновляем pip
    # docker exec "${CONTAINER_NAME}" python3 -m pip install --upgrade pip --user
    
    # # Устанавливаем пакеты по одному
    # log_info "Установка loguru..."
    # if docker exec "${CONTAINER_NAME}" python3 -m pip install --user loguru; then
    #     log_success "loguru установлен"
    # else
    #     log_warning "Ошибка установки loguru"
    # fi
    
    # log_info "Установка nodriver..."
    # if docker exec "${CONTAINER_NAME}" python3 -m pip install --user nodriver; then
    #     log_success "nodriver установлен"
    # else
    #     log_warning "Ошибка установки nodriver, пробуем альтернативный способ..."
    #     docker exec "${CONTAINER_NAME}" python3 -m pip install --user --no-deps nodriver
    # fi
    install_chrome_in_container
    # 6. Установка зависимостей для сбора данных на хосте
    log_step "Установка зависимостей для сбора данных..."
    check_data_collection_deps
    
    # 7. Копирование скрипта
    if copy_auth_script; then
        log_success "Скрипт скопирован"
    else
        log_error "Ошибка копирования скрипта"
        set -e
        return 1
    fi
    
    # 8. Финальная проверка
    log_step "Финальная проверка готовности системы..."
    
    # Проверяем Chrome (с таймаутом)
    log_info "Проверка Chrome..."
    for i in {1..10}; do
        if docker exec "${CONTAINER_NAME}" pgrep -f "chrome" > /dev/null 2>&1; then
            log_success "Chrome запущен и готов"
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""
    
    # Проверяем Python скрипт
    if docker exec "${CONTAINER_NAME}" test -f "/workspace/app/auth_gui.py"; then
        log_success "Скрипт авторизации готов"
    else
        log_error "Скрипт авторизации не найден"
        set -e
        return 1
    fi
    
    log_success "🎉 Настройка завершена! Система готова к работе."
    
    # Возвращаем set -e
    set -e
    return 0
}

fix_permissions() {
    log_step "Исправление прав доступа..."
    
    # Исправляем права на папку cookies в контейнере (ИЗМЕНЕНО: ubuntu вместо seluser)
    log_info "Исправление прав на папку cookies в контейнере..."
    docker exec --user root "${CONTAINER_NAME}" bash -c "
        mkdir -p /home/ubuntu/tikleap_work/cookies &&
        chown -R ubuntu:ubuntu /home/ubuntu/tikleap_work &&
        chmod -R 755 /home/ubuntu/tikleap_work
    "
    
    # Также исправляем права на хост-системе
    log_info "Исправление прав на хост-папку cookies..."
    chmod -R 777 "${COOKIES_DIR}" 2>/dev/null || true
    
    log_success "Права доступа исправлены"
}

# Альтернативная функция - только установка без авторизации
setup_only() {
    log_step "🔧 Только настройка без авторизации"
    
    if auto_setup_and_install; then
        log_success "✅ Настройка завершена. Для авторизации используйте: $0 --auth"
    else
        log_error "❌ Ошибка при настройке"
        return 1
    fi
}

# Запуск авторизации
run_auth() {
    log_step "Запуск процесса авторизации..."
    
    echo -e "\n${CYAN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}🤖 АВТОМАТИЧЕСКАЯ АВТОРИЗАЦИЯ${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅${NC} VNC доступен по адресу: ${BLUE}${VNC_URL}${NC}"
    echo -e "${GREEN}✅${NC} Пароль для VNC: ${YELLOW}${VNC_PASSWORD}${NC}"
    echo -e "${GREEN}✅${NC} Автоматические данные для входа:"
    echo -e "   ${CYAN}Email:${NC} 37200@starlivemail.com"
    echo -e "   ${CYAN}Пароль:${NC} bfnsa232@1!dsA"
    echo -e "${GREEN}🔄${NC} Запуск автоматической авторизации..."
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}\n"
    
    # Автоматическое открытие браузера (для macOS/Linux)
    if command -v open &> /dev/null; then
        log_info "Открытие VNC в браузере..."
        open "${VNC_URL}" 2>/dev/null || true
    elif command -v xdg-open &> /dev/null; then
        log_info "Открытие VNC в браузере..."
        xdg-open "${VNC_URL}" 2>/dev/null || true
    fi
    
    # Автоматический запуск скрипта авторизации (без интерактивного режима)
    log_info "Запуск автоматической авторизации (таймаут 60 секунд)..."
    docker exec "${CONTAINER_NAME}" python3 /workspace/app/auth_gui.py
    
    # Проверка результата
    sleep 5
    log_info "Проверка результатов авторизации..."
    
    if [ -f "${COOKIES_DIR}/cookies_important.json" ]; then
        log_success "🎉 Авторизация завершена! Cookies сохранены."
        check_cookies
        return 0
    else
        log_warning "⚠️  Cookies не найдены. Возможно, потребуется ручная авторизация через VNC."
        log_info "Откройте ${VNC_URL} для ручной авторизации при необходимости."
        return 1
    fi
}

# Полный цикл: авторизация + сбор данных
run_full_cycle() {
    log_step "🔄 Запуск полного цикла: авторизация + сбор данных"
    
    # Шаг 1: Авторизация
    if run_auth; then
        log_success "✅ Авторизация завершена успешно"
    else
        log_error "❌ Ошибка авторизации"
        return 1
    fi
    
    # Небольшая пауза
    log_info "⏳ Пауза 5 секунд между авторизацией и сбором данных..."
    sleep 5
    
    # Шаг 2: Сбор данных
    if run_data_collection; then
        log_success "🎉 Полный цикл завершен успешно!"
        return 0
    else
        log_error "❌ Ошибка сбора данных"
        return 1
    fi
}

# Планировщик для запуска каждые N минут
run_scheduler() {
    local interval_minutes=${1:-5}
    log_step "⏰ Запуск планировщика каждые $interval_minutes минут"
    
    local cycle_count=0
    
    while true; do
        cycle_count=$((cycle_count + 1))
        log_info "🔢 Цикл #$cycle_count"
        
        if run_full_cycle; then
            log_success "✅ Цикл #$cycle_count завершен успешно"
        else
            log_error "❌ Цикл #$cycle_count завершен с ошибкой"
        fi
        
        log_info "😴 Ожидание $interval_minutes минут до следующего цикла..."
        sleep $((interval_minutes * 60))
    done
}

# Проверка сохраненных cookies
check_cookies() {
    log_step "Проверка сохраненных cookies..."
    
    if [ ! -d "${COOKIES_DIR}" ]; then
        log_warning "Папка cookies не существует"
        return 1
    fi
    
    local important_file="${COOKIES_DIR}/cookies_important.json"
    local session_file="${COOKIES_DIR}/browser_session.dat"
    
    if [ -f "${important_file}" ]; then
        log_success "Найден файл важных cookies: ${important_file}"
        
        # Проверка размера файла
        local file_size=$(stat -f%z "${important_file}" 2>/dev/null || stat -c%s "${important_file}" 2>/dev/null || echo "0")
        log_info "Размер файла: $file_size байт"
        
        if [ "$file_size" -gt 0 ]; then
            log_success "Cookies файл не пустой"
        else
            log_warning "Cookies файл пустой"
        fi
    else
        log_warning "Файл важных cookies не найден"
    fi
    
    if [ -f "${session_file}" ]; then
        log_success "Найден файл сессии браузера: ${session_file}"
    else
        log_warning "Файл сессии браузера не найден"
    fi
    
    # Показать все файлы cookies
    echo -e "\n${CYAN}📁 Содержимое папки cookies:${NC}"
    ls -la "${COOKIES_DIR}" || echo "Папка пуста"
}

# Очистка cookies
clean_cookies() {
    log_step "Очистка старых cookies..."
    
    if [ -d "${COOKIES_DIR}" ]; then
        rm -rf "${COOKIES_DIR}"/*
        log_success "Cookies очищены"
    else
        log_info "Папка cookies не существует"
    fi
}

# Показать логи контейнера
show_logs() {
    log_step "Показ логов контейнера..."
    
    docker logs -f --tail=50 "${CONTAINER_NAME}"
}

# Главное меню
show_menu() {
    echo -e "\n${PURPLE}🎬 TikLeap Authentication & Data Collection Manager${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}1.${NC} 🚀 Полный запуск (настройка + авторизация + сбор данных)"
    echo -e "${GREEN}2.${NC} 🔄 Один цикл (авторизация + сбор данных)"
    echo -e "${GREEN}3.${NC} ⏰ Планировщик (каждые N минут)"
    echo -e "${GREEN}4.${NC} 🔧 Только создать структуру и контейнер"
    echo -e "${GREEN}5.${NC} ▶️  Запустить контейнер"
    echo -e "${GREEN}6.${NC} 🔐 Только авторизация"
    echo -e "${GREEN}7.${NC} 📊 Только сбор данных"
    echo -e "${GREEN}8.${NC} 🍪 Проверить cookies"
    echo -e "${GREEN}9.${NC} 🗑️  Очистить cookies"
    echo -e "${GREEN}10.${NC} 📋 Показать логи"
    echo -e "${GREEN}11.${NC} ⏹️  Остановить контейнер"
    echo -e "${GREEN}12.${NC} ❌ Выход"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
}

# Полный запуск
full_setup() {
    log_step "🎯 Полный автоматический запуск TikLeap"
    
    # Автоматическая настройка всего
    if auto_setup_and_install; then
        echo -e "\n${GREEN}✅ Все готово!${NC}"
        
        # Автоматический запуск полного цикла
        log_info "Запуск полного цикла через 3 секунды..."
        sleep 3
        run_full_cycle
    else
        log_error "❌ Ошибка при настройке. Проверьте логи."
        return 1
    fi
}

# Обработка аргументов командной строки
case "${1:-menu}" in
    -f|--full|full)
        full_setup
        ;;
    -c|--cycle|cycle)
        # Проверяем что система настроена
        if [ ! -f "${SCRIPT_DIR}/docker-compose.yml" ]; then
            log_error "Система не настроена. Запустите: $0 --setup"
            exit 1
        fi
        run_full_cycle
        ;;
    -p|--scheduler|scheduler)
        # Планировщик с интервалом
        interval=${2:-5}
        if ! [[ "$interval" =~ ^[0-9]+$ ]] || [ "$interval" -lt 1 ]; then
            log_error "Неверный интервал: $interval (должно быть положительное число)"
            exit 1
        fi
        run_scheduler "$interval"
        ;;
    -s|--setup|setup)
        setup_only
        ;;
    -auto|--auto|auto)
        auto_setup_and_install
        ;;
    -u|--up|up|start)
        start_container
        ;;
    -a|--auth|auth)
        install_dependencies
        copy_auth_script
        run_auth
        ;;
    -d|--data|data)
        run_data_collection
        ;;
    --check|check)
        check_cookies
        ;;
    -clean|--clean|clean)
        clean_cookies
        ;;
    -l|--logs|logs)
        show_logs
        ;;
    --down|down|stop)
        stop_container
        ;;
    -h|--help|help)
        echo "TikLeap Authentication & Data Collection Manager"
        echo ""
        echo "Использование: $0 [КОМАНДА] [ОПЦИИ]"
        echo ""
        echo "Команды:"
        echo "  -f, --full         Полный автоматический запуск"
        echo "  -c, --cycle        Один цикл (авторизация + сбор данных)"
        echo "  -p, --scheduler N  Планировщик каждые N минут (по умолчанию 5)"
        echo "  -s, --setup        Только установка без авторизации"
        echo "  --auto             Автоустановка всех зависимостей"
        echo "  -u, --up           Запустить контейнер"
        echo "  -a, --auth         Только авторизация"
        echo "  -d, --data         Только сбор данных"
        echo "  --check            Проверить cookies"
        echo "  --clean            Очистить cookies"
        echo "  -l, --logs         Показать логи"
        echo "  --down             Остановить контейнер"
        echo "  -h, --help         Показать помощь"
        echo ""
        echo "Примеры:"
        echo "  $0 --full          # Полная настройка и запуск"
        echo "  $0 --cycle         # Один цикл авторизация+сбор"
        echo "  $0 --scheduler 10  # Каждые 10 минут"
        echo ""
        echo "Без аргументов - интерактивное меню"
        ;;
    menu|*)
        while true; do
            show_menu
            read -p "Выберите действие (1-12): " choice
            
            case $choice in
                1)
                    full_setup
                    ;;
                2)
                    run_full_cycle
                    ;;
                3)
                    read -p "Введите интервал в минутах (по умолчанию 5): " interval
                    interval=${interval:-5}
                    run_scheduler "$interval"
                    ;;
                4)
                    setup_only
                    ;;
                5)
                    start_container
                    ;;
                6)
                    install_dependencies
                    copy_auth_script
                    run_auth
                    ;;
                7)
                    run_data_collection
                    ;;
                8)
                    check_cookies
                    ;;
                9)
                    clean_cookies
                    ;;
                10)
                    show_logs
                    ;;
                11)
                    stop_container
                    ;;
                12)
                    log_info "До свидания!"
                    exit 0
                    ;;
                *)
                    log_error "Неверный выбор. Пожалуйста, выберите 1-12."
                    ;;
            esac
            
            echo ""
            read -p "Нажмите Enter для продолжения..."
        done
        ;;
esac