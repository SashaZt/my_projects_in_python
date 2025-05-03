#!/bin/bash
# 
# Скрипт для управления Docker-контейнерами проекта
#

# Функция для отображения помощи
show_help() {
  echo "Использование: $0 [ОПЦИЯ]"
  echo "Опции:"
  echo "  start              - Запустить все контейнеры (по умолчанию)"
  echo "  stop               - Остановить все контейнеры"
  echo "  restart            - Перезапустить все контейнеры"
  echo "  restart-parser     - Перезапустить только контейнер parser"
  echo "  restart-importer   - Перезапустить только контейнер importer"
  echo "  restart-postgres   - Перезапустить только контейнер postgres"
  echo "  reload-config      - Перегенерировать .env из config.json и перезапустить контейнеры"
  echo "  update-env KEY=VALUE - Обновить значение переменной в .env файле и перезапустить соответствующие контейнеры"
  echo "  update-env-only KEY=VALUE - Обновить переменную в .env без перезапуска контейнеров"
  echo "  update-multi-env KEY1=VALUE1 KEY2=VALUE2... - Обновить несколько переменных и перезапустить все контейнеры"
  echo "  toggle-mode        - Переключить режим между CAR_PARTS=true и CAR_PARTS=false"
  echo "  update-category ID - Обновить ID категории в config.json и перезапустить parser"
  echo "  update-config KEY VALUE - Обновить любой параметр в config.json и перезапустить контейнеры"
  echo "  logs               - Показать логи всех контейнеров"
  echo "  logs-parser        - Показать логи parser"
  echo "  logs-importer      - Показать логи importer"
  echo "  logs-postgres      - Показать логи postgres"
  echo "  help               - Показать эту справку"
}

# Перегенерировать .env из config.json
generate_env() {
  # Проверка наличия config.json
  if [ ! -f "config.json" ]; then
    echo "Ошибка: файл config.json не найден!"
    exit 1
  fi

  # Генерация .env файла из config.json
  echo "Генерация переменных окружения из config.json..."
  python3 config_loader.py config.json .env

  # Проверка результата
  if [ $? -ne 0 ]; then
    echo "Ошибка при генерации .env файла!"
    exit 1
  fi
  
  echo ".env файл успешно сгенерирован."
}

# Функция для обновления переменной в .env файле без перезапуска контейнеров
update_env_variable_only() {
  local key_value="$1"
  local key="${key_value%%=*}"
  local value="${key_value#*=}"
  
  # Проверяем, существует ли .env файл
  if [ ! -f ".env" ]; then
    echo "Ошибка: .env файл не найден. Сначала запустите 'reload-config'"
    exit 1
  fi

  echo "Обновление переменной $key в .env файле..."
  
  # Проверяем, существует ли переменная в .env
  if grep -q "^$key=" .env; then
    # Если значение содержит специальные символы, экранируем их для sed
    value_escaped=$(echo "$value" | sed 's/[\/&]/\\&/g')
    # Заменяем значение
    sed -i "s/^$key=.*/$key=$value_escaped/" .env
  else
    # Добавляем новую переменную
    echo "$key=$value" >> .env
  fi
  
  echo "Переменная $key успешно обновлена. Контейнеры не перезапущены."
}
update_parser_threads() {
    local threads="$1"
    echo "$(jq ".parser.max_threads = $threads" config.json)" > config.json
    echo "Максимальное количество потоков обновлено на $threads"
    
    # Регенерируем .env и перезапускаем parser
    generate_env
    echo "Перезапуск parser..."
    docker compose stop parser
    docker compose rm -f parser
    docker compose up -d parser
}

# Обновление ID категории
update_parser_category() {
    local category_id="$1"
    echo "$(jq ".parser.id_category = $category_id" config.json)" > config.json
    echo "ID категории обновлен на $category_id"
    
    # Регенерируем .env и перезапускаем parser
    generate_env
    echo "Перезапуск parser..."
    docker compose stop parser
    docker compose rm -f parser
    docker compose up -d parser
}

# Обновление минимальной цены
update_parser_price_from() {
    local price="$1"
    echo "$(jq ".parser.price_from = \"$price\"" config.json)" > config.json
    echo "Минимальная цена обновлена на $price"
    
    # Регенерируем .env и перезапускаем parser
    generate_env
    echo "Перезапуск parser..."
    docker compose stop parser
    docker compose rm -f parser
    docker compose up -d parser
}

# Обновление режима car_parts
update_parser_car_parts() {
    local enabled="$1"
    if [[ "$enabled" != "true" && "$enabled" != "false" ]]; then
        echo "Ошибка: значение должно быть true или false"
        exit 1
    fi
    
    echo "$(jq ".parser.car_parts = $enabled" config.json)" > config.json
    
    if [ "$enabled" = "true" ]; then
        echo "Режим обработки автозапчастей включен"
    else
        echo "Режим обработки всей категории включен"
    fi
    
    # Регенерируем .env и перезапускаем parser и importer
    generate_env
    echo "Перезапуск parser и importer..."
    docker compose stop parser importer
    docker compose rm -f parser importer
    docker compose up -d parser importer
}




# Функция для обновления переменной в .env файле и перезапуска соответствующих контейнеров
update_env_variable() {
  local key_value="$1"
  local key="${key_value%%=*}"
  local value="${key_value#*=}"
  
  # Обновляем переменную без перезапуска
  update_env_variable_only "$key_value"
  
  # Определяем, какие контейнеры нужно перезапустить
  local restart_containers=""
  case "$key" in
    PARSER_*|MAX_THREADS)
      restart_containers="auto_parts_database-parser"
      ;;
    CAR_PARTS)
      restart_containers="auto_parts_database-parser auto_parts_database-importer"
      ;;
    IMPORTER_*|WATCH_DIR|CHECK_INTERVAL|INITIAL_SCAN)
      restart_containers="auto_parts_database-importer"
      ;;
    POSTGRES_*|PG_*)
      restart_containers="auto_parts_database-postgres"
      ;;
    *)
      # Для других переменных перезапускаем все контейнеры
      restart_containers="auto_parts_database-parser auto_parts_database-importer auto_parts_database-postgres"
      ;;
  esac
  
  # Перезапускаем соответствующие контейнеры
  for container in $restart_containers; do
    echo "Перезапуск контейнера $container..."
    docker restart $container
    if [ $? -eq 0 ]; then
      echo "Контейнер $container успешно перезапущен."
    else
      echo "Ошибка при перезапуске контейнера $container."
    fi
  done
}

# Функция для обновления нескольких переменных сразу
update_multi_env() {
  local updated=false
  
  while [ "$#" -gt 0 ]; do
    local key_value="$1"
    update_env_variable_only "$key_value"
    updated=true
    shift
  done
  
  if $updated; then
    echo "Перезапуск всех контейнеров для применения новых настроек..."
    docker compose restart
    echo "Все контейнеры перезапущены."
  else
    echo "Не указаны переменные для обновления. Пример: $0 update-multi-env VAR1=value1 VAR2=value2"
  fi
}
# Функция для выборочного обновления параметров parser
update_parser_selective() {
    local updated=false
    local need_restart=false
    
    # Перебираем все параметры в формате ключ=значение
    while [ "$#" -gt 0 ]; do
        local param="$1"
        local key="${param%%=*}"
        local value="${param#*=}"
        
        case "$key" in
            threads)
                echo "$(jq ".parser.max_threads = $value" config.json)" > config.json
                echo "Максимальное количество потоков обновлено на $value"
                updated=true
                need_restart=true
                ;;
            category)
                echo "$(jq ".parser.id_category = $value" config.json)" > config.json
                echo "ID категории обновлен на $value"
                updated=true
                need_restart=true
                ;;
            price)
                echo "$(jq ".parser.price_from = \"$value\"" config.json)" > config.json
                echo "Минимальная цена обновлена на $value"
                updated=true
                need_restart=true
                ;;
            car_parts)
                if [[ "$value" != "true" && "$value" != "false" ]]; then
                    echo "Ошибка: значение car_parts должно быть true или false"
                    continue
                fi
                echo "$(jq ".parser.car_parts = $value" config.json)" > config.json
                if [ "$value" = "true" ]; then
                    echo "Режим обработки автозапчастей включен"
                else
                    echo "Режим обработки всей категории включен"
                fi
                updated=true
                # Для car_parts нужно перезапустить и parser, и importer
                need_restart=true
                ;;
            *)
                echo "Неизвестный параметр: $key"
                echo "Доступные параметры: threads, category, price, car_parts"
                ;;
        esac
        
        shift
    done
    
    if $updated; then
        # Регенерируем .env
        generate_env
        
        if $need_restart; then
            # Перезапускаем необходимые сервисы
            echo "Перезапуск parser..."
            docker compose stop parser
            docker compose rm -f parser
            docker compose up -d parser
            
            # Если обновляли car_parts, перезапускаем и importer
            if grep -q '"car_parts": false' config.json || grep -q '"car_parts": true' config.json; then
                echo "Перезапуск importer..."
                docker compose stop importer
                docker compose rm -f importer
                docker compose up -d importer
            fi
        fi
    else
        echo "Не указаны параметры для обновления."
        echo "Пример использования: $0 update-parser category=260617 price=100 threads=50 car_parts=true"
    fi
}

# Функция для проверки и настройки директории данных PostgreSQL
check_postgres_data_dir() {
  # Загружаем переменные окружения из .env файла
  source .env
  PG_DATA_DIR=${POSTGRES_DATA_DIR:-./pgdata}

  # Проверяем наличие директории данных
  if [ ! -d "$PG_DATA_DIR" ]; then
    echo "Создание директории для данных PostgreSQL: $PG_DATA_DIR"
    mkdir -p "$PG_DATA_DIR"
    
    # Устанавливаем правильные права доступа для пользователя postgres (UID 999)
    echo "Установка прав доступа для директории данных PostgreSQL..."
    sudo chown -R 999:999 "$PG_DATA_DIR"
  else
    echo "Директория для данных PostgreSQL уже существует: $PG_DATA_DIR"
    
    # Проверяем права доступа и исправляем их при необходимости
    if [ "$(stat -c '%u:%g' "$PG_DATA_DIR")" != "999:999" ]; then
      echo "Исправление прав доступа для директории данных PostgreSQL..."
      sudo chown -R 999:999 "$PG_DATA_DIR"
    fi
    
    # Проверяем, есть ли там уже данные PostgreSQL
    if [ -f "$PG_DATA_DIR/PG_VERSION" ]; then
      echo "Обнаружена существующая база данных PostgreSQL"
      echo "Установка POSTGRES_INIT_DB=false для предотвращения повторной инициализации"
      sed -i 's/POSTGRES_INIT_DB=true/POSTGRES_INIT_DB=false/' .env
    fi
  fi
}

# Функция для запуска всех контейнеров
start_containers() {
  echo "Запуск контейнеров..."
  
  # В режиме разработки добавляем флаг build для пересборки образов
  if grep -q '"environment": *"development"' config.json; then
    docker compose up -d --build
  else
    docker compose up -d
  fi
  
  echo "Проверка статуса контейнеров..."
  docker compose ps
  
  echo "Система запущена! Для просмотра логов используйте './start.sh logs'"
}

# Функция для отображения логов
show_logs() {
  local service="$1"
  
  if [ -z "$service" ]; then
    docker compose logs -f
  else
    docker compose logs -f "$service"
  fi
}

# Основная логика скрипта
COMMAND=${1:-start}

case "$COMMAND" in
  start)
    generate_env
    check_postgres_data_dir
    start_containers
    ;;
  stop)
    echo "Остановка контейнеров..."
    docker compose down
    echo "Контейнеры остановлены."
    ;;
  restart)
    echo "Перезапуск всех контейнеров..."
    docker compose restart
    echo "Все контейнеры перезапущены."
    ;;
  restart-parser)
    echo "Перезапуск контейнера parser..."
    docker restart auto_parts_database-parser
    echo "Контейнер parser перезапущен."
    ;;
  restart-importer)
    echo "Перезапуск контейнера importer..."
    docker restart auto_parts_database-importer
    echo "Контейнер importer перезапущен."
    ;;
  restart-postgres)
    echo "Перезапуск контейнера postgres..."
    docker restart auto_parts_database-postgres
    echo "Контейнер postgres перезапущен."
    ;;
  reload-config)
    generate_env
    echo "Перезапуск всех контейнеров для применения новой конфигурации..."
    docker compose restart
    echo "Конфигурация перезагружена и контейнеры перезапущены."
    ;;
  update-env)
    if [ -z "$2" ]; then
      echo "Ошибка: не указано значение переменной для обновления."
      echo "Пример использования: $0 update-env PARSER_ID_CATEGORY=123456"
      exit 1
    fi
    update_env_variable "$2"
    ;;
  update-env-only)
    if [ -z "$2" ]; then
      echo "Ошибка: не указано значение переменной для обновления."
      echo "Пример использования: $0 update-env-only PARSER_ID_CATEGORY=123456"
      exit 1
    fi
    update_env_variable_only "$2"
    ;;
  update-multi-env)
    shift
    update_multi_env "$@"
    ;;

  logs)
    show_logs
    ;;
  logs-parser)
    show_logs "parser"
    ;;
  logs-importer)
    show_logs "importer"
    ;;
  logs-postgres)
    show_logs "postgres"
    ;;
  update-parser)
    shift
    if [ "$#" -eq 0 ]; then
        echo "Ошибка: не указаны параметры для обновления."
        echo "Пример использования: $0 update-parser category=260617 price=100 threads=50 car_parts=true"
        exit 1
    fi
    update_parser_selective "$@"
    ;;
  update-category)
    if [ -z "$2" ]; then
        echo "Ошибка: не указан ID категории."
        echo "Пример использования: $0 update-category 260617"
        exit 1
    fi
    update_parser_category "$2"
    ;;

  update-config)
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo "Ошибка: не указаны параметры."
        echo "Пример использования: $0 update-config parser.id_category 260617"
        exit 1
    fi
    update_config_json "$2" "$3"
    # После обновления конфигурации перезапускаем все контейнеры
    echo "Перезапуск всех контейнеров для применения новых настроек..."
    docker compose down
    docker compose up -d
    ;;
    car-parts)
    if [ -z "$2" ]; then
        echo "Ошибка: не указано значение (true/false)."
        echo "Пример использования: $0 car-parts true"
        exit 1
    fi
    update_parser_car_parts "$2"
    ;;
  help)
    show_help
    ;;
  *)
    echo "Неизвестная команда: $COMMAND"
    show_help
    exit 1
    ;;
esac