#client/Dockerfile
FROM python:3.12-slim

WORKDIR /client

# Устанавливаем bash для выполнения скриптов
RUN apt-get update && apt-get install -y bash && apt-get clean

# Копируем requirements.txt, если он есть
COPY requirements.txt* ./

# Устанавливаем зависимости, если файл существует
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Копируем весь код
COPY . .

# Создаем папку для монтированных файлов
RUN mkdir -p /client

# Запуск с обработкой сигналов
CMD ["python", "main_controller.py"]