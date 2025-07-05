#!/bin/bash

# =============================================================================
# 🎯 TikLeap Authentication Manager
# Объединенный скрипт для управления Docker авторизацией
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
VNC_URL="http://localhost:7900"
VNC_PASSWORD="secret"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COOKIES_DIR="${SCRIPT_DIR}/cookies"
APP_DIR="${SCRIPT_DIR}/app"

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
    
    log_success "Все зависимости установлены"
}

# Создание структуры папок
create_structure() {
    log_step "Создание структуры директорий..."
    
    mkdir -p "${APP_DIR}" "${COOKIES_DIR}" "${SCRIPT_DIR}/data"
    
    log_success "Структура создана: ${SCRIPT_DIR}"
}

# Создание docker-compose.yml
create_docker_compose() {
    log_step "Создание docker-compose.yml..."
    
    cat > "${SCRIPT_DIR}/docker-compose.yml" << 'EOF'
services:
  nodriver-auth:
    image: selenium/standalone-chrome:4.15.0
    container_name: nodriver-manual-auth
    ports:
      - "4444:4444"    # Selenium Grid порт
      - "7900:7900"    # noVNC веб-интерфейс
    volumes:
      - ./app:/workspace/app
      - ./cookies:/home/seluser/tikleap_work/cookies
      - ./data:/workspace/data
    environment:
      - SE_SCREEN_WIDTH=1920
      - SE_SCREEN_HEIGHT=1080
      - SE_VNC_PASSWORD=secret
      - SE_START_XVFB=true
    restart: unless-stopped
    shm_size: 2gb
EOF
    
    log_success "docker-compose.yml создан"
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
# Полная автоматическая настройка и установка
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
    if docker exec --user root "${CONTAINER_NAME}" bash -c "apt-get update"; then
        log_success "Пакеты обновлены"
    else
        log_error "Ошибка обновления пакетов"
        set -e
        return 1
    fi
    
    log_info "📦 Установка системных зависимостей..."
    if docker exec --user root "${CONTAINER_NAME}" bash -c "apt-get install -y python3-pip wget curl"; then
        log_success "Системные пакеты установлены"
    else
        log_error "Ошибка установки системных пакетов"
        set -e
        return 1
    fi
    
    log_info "🐍 Проверка Python и pip..."
    docker exec "${CONTAINER_NAME}" python3 --version
    docker exec "${CONTAINER_NAME}" pip3 --version
    
    log_info "📚 Установка Python зависимостей..."
    # Сначала обновляем pip
    docker exec "${CONTAINER_NAME}" python3 -m pip install --upgrade pip --user
    
    # Устанавливаем пакеты по одному
    log_info "Установка loguru..."
    if docker exec "${CONTAINER_NAME}" python3 -m pip install --user loguru; then
        log_success "loguru установлен"
    else
        log_warning "Ошибка установки loguru"
    fi
    
    log_info "Установка nodriver..."
    if docker exec "${CONTAINER_NAME}" python3 -m pip install --user nodriver; then
        log_success "nodriver установлен"
    else
        log_warning "Ошибка установки nodriver, пробуем альтернативный способ..."
        docker exec "${CONTAINER_NAME}" python3 -m pip install --user --no-deps nodriver
    fi
    
    # 6. Проверка установки
    log_step "Проверка установленных зависимостей..."
    
    # Проверяем каждый модуль отдельно
    log_info "Проверка loguru..."
    if docker exec "${CONTAINER_NAME}" python3 -c "import loguru; print('✅ loguru работает')"; then
        log_success "loguru работает"
    else
        log_warning "loguru не работает"
    fi
    
    log_info "Проверка nodriver..."
    if docker exec "${CONTAINER_NAME}" python3 -c "import nodriver; print('✅ nodriver работает')"; then
        log_success "nodriver работает"
    else
        log_warning "nodriver не работает"
    fi
    
    # Финальная проверка
    log_info "Финальная проверка всех модулей..."
    if docker exec "${CONTAINER_NAME}" python3 -c "
import sys
success = True

try:
    import loguru
    print('✅ loguru: OK')
except Exception as e:
    print(f'❌ loguru: {e}')
    success = False

try:
    import nodriver
    print('✅ nodriver: OK')
except Exception as e:
    print(f'❌ nodriver: {e}')
    success = False

if success:
    print('🎉 Все модули работают!')
else:
    print('⚠️ Некоторые модули не работают, но продолжаем...')
"; then
        log_success "Проверка модулей завершена"
    else
        log_warning "Проблемы с модулями, но продолжаем..."
    fi
    
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
    
    # Исправляем права на папку cookies в контейнере
    log_info "Исправление прав на папку cookies в контейнере..."
    docker exec --user root "${CONTAINER_NAME}" bash -c "
        mkdir -p /home/seluser/tikleap_work/cookies &&
        chown -R seluser:seluser /home/seluser/tikleap_work &&
        chmod -R 755 /home/seluser/tikleap_work
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
    else
        log_warning "⚠️  Cookies не найдены. Возможно, потребуется ручная авторизация через VNC."
        log_info "Откройте ${VNC_URL} для ручной авторизации при необходимости."
    fi
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
        
        # Проверка срока действия
        if command -v python3 &> /dev/null; then
            local expires_check=$(python3 -c "
import json
import datetime
try:
    with open('${important_file}', 'r') as f:
        data = json.load(f)
    expires_at = datetime.datetime.fromisoformat(data.get('expires_at', ''))
    if datetime.datetime.now() < expires_at:
        print('valid')
    else:
        print('expired')
except:
    print('error')
" 2>/dev/null)
            
            case $expires_check in
                "valid")
                    log_success "Cookies действительны"
                    ;;
                "expired")
                    log_warning "Cookies истекли, нужна повторная авторизация"
                    ;;
                *)
                    log_warning "Не удалось проверить срок действия cookies"
                    ;;
            esac
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
    echo -e "\n${PURPLE}🎬 TikLeap Authentication Manager${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}1.${NC} 🚀 Полный запуск (создать + запустить + авторизоваться)"
    echo -e "${GREEN}2.${NC} 🔧 Только создать структуру и контейнер"
    echo -e "${GREEN}3.${NC} ▶️  Запустить контейнер"
    echo -e "${GREEN}4.${NC} 🔐 Запустить авторизацию"
    echo -e "${GREEN}5.${NC} 🍪 Проверить cookies"
    echo -e "${GREEN}6.${NC} 🗑️  Очистить cookies"
    echo -e "${GREEN}7.${NC} 📋 Показать логи"
    echo -e "${GREEN}8.${NC} ⏹️  Остановить контейнер"
    echo -e "${GREEN}9.${NC} ❌ Выход"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
}

# Полный запуск
full_setup() {
    log_step "🎯 Полный автоматический запуск TikLeap Authentication"
    
    # Автоматическая настройка всего
    if auto_setup_and_install; then
        echo -e "\n${GREEN}✅ Все готово к авторизации!${NC}"
        
        # Автоматический запуск авторизации без ожидания
        log_info "Запуск авторизации через 3 секунды..."
        sleep 3
        run_auth
    else
        log_error "❌ Ошибка при настройке. Проверьте логи."
        return 1
    fi
}

# Обработка аргументов командной строки
case "${1:-menu}" in
    -f|--full|full)
        full_setup  # Эта функция уже определена выше с auto_setup_and_install
        ;;
    -s|--setup|setup)
        setup_only  # Используем новую функцию только для установки
        ;;
    -auto|--auto|auto)
        auto_setup_and_install  # Только автоустановка
        ;;
    -u|--up|up|start)
        start_container
        ;;
    -a|--auth|auth)
        install_dependencies
        copy_auth_script
        run_auth
        ;;
    -c|--check|check)
        check_cookies
        ;;
    -clean|--clean|clean)
        clean_cookies
        ;;
    -l|--logs|logs)
        show_logs
        ;;
    -d|--down|down|stop)
        stop_container
        ;;
    -h|--help|help)
        echo "Использование: $0 [КОМАНДА]"
        echo ""
        echo "Команды:"
        echo "  -f, --full     Полный автоматический запуск"
        echo "  -s, --setup    Только установка без авторизации"
        echo "  --auto         Автоустановка всех зависимостей"
        echo "  -u, --up       Запустить контейнер"
        echo "  -a, --auth     Запустить авторизацию"
        echo "  -c, --check    Проверить cookies"
        echo "  --clean        Очистить cookies"
        echo "  -l, --logs     Показать логи"
        echo "  -d, --down     Остановить контейнер"
        echo "  -h, --help     Показать помощь"
        echo ""
        echo "Без аргументов - интерактивное меню"
        ;;
    menu|*)
        while true; do
            show_menu
            read -p "Выберите действие (1-9): " choice
            
            case $choice in
                1)
                    full_setup  # Автоматическая версия
                    ;;
                2)
                    setup_only  # Только установка
                    ;;
                3)
                    start_container
                    ;;
                4)
                    install_dependencies
                    copy_auth_script
                    run_auth
                    ;;
                5)
                    check_cookies
                    ;;
                6)
                    clean_cookies
                    ;;
                7)
                    show_logs
                    ;;
                8)
                    stop_container
                    ;;
                9)
                    log_info "До свидания!"
                    exit 0
                    ;;
                *)
                    log_error "Неверный выбор. Пожалуйста, выберите 1-9."
                    ;;
            esac
            
            echo ""
            read -p "Нажмите Enter для продолжения..."
        done
        ;;
esac