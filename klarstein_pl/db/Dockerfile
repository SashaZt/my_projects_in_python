# postgres/Dockerfile
FROM postgres:17

# Устанавливаем необходимые пакеты
RUN apt-get update && \
    apt-get install -y \
    tzdata \
    locales \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копируем скрипты инициализации
COPY init-scripts/ /docker-entrypoint-initdb.d/

# Делаем скрипты исполняемыми
RUN chmod +x /docker-entrypoint-initdb.d/*.sh

# Используем стандартный CMD PostgreSQL
CMD ["postgres"]

HEALTHCHECK --interval=30s --timeout=10s --retries=5 \
    CMD pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-postgres} || exit 1