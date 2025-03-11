# postgres/Dockerfile
FROM postgres:17

LABEL maintainer="your-email@example.com"
LABEL version="1.0"


# Оптимизировать настройки PostgreSQL для продакшена
CMD ["postgres", \
    "-c", "max_connections=200", \
    "-c", "shared_buffers=512MB", \
    "-c", "effective_cache_size=1536MB", \
    "-c", "maintenance_work_mem=128MB", \
    "-c", "checkpoint_completion_target=0.9", \
    "-c", "wal_buffers=16MB", \
    "-c", "default_statistics_target=100", \
    "-c", "random_page_cost=1.1", \
    "-c", "effective_io_concurrency=200", \
    "-c", "work_mem=6553kB", \
    "-c", "min_wal_size=1GB", \
    "-c", "max_wal_size=4GB"]

HEALTHCHECK --interval=30s --timeout=10s --retries=5 \
    CMD pg_isready -U $POSTGRES_USER -d $POSTGRES_DB || exit 1