FROM postgres:16

# Копируем скрипты инициализации
COPY init-scripts/ /docker-entrypoint-initdb.d/

# Используем стандартный CMD PostgreSQL
CMD ["postgres"]

HEALTHCHECK --interval=30s --timeout=10s --retries=5 \
    CMD pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-postgres} || exit 1