FROM minio/minio:latest

# Метаданные
LABEL maintainer="user@example.com"
LABEL description="MinIO S3-совместимое хранилище для маркетплейсов"
LABEL version="1.0"

# Порты (API и консоль)
EXPOSE 9000 9001

# Директория для данных
VOLUME ["/data"]

# Запуск MinIO сервера
ENTRYPOINT ["minio"]
CMD ["server", "--console-address", ":9001", "/data"]

# Проверка здоровья
HEALTHCHECK --interval=30s --timeout=5s \
    CMD curl -f http://localhost:9000/minio/health/live || exit 1