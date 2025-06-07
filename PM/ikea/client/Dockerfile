# client/Dockerfile
FROM python:3.12-slim

WORKDIR /client

RUN apt-get update 

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /client

RUN mkdir -p /client/temp && chmod 755 /client/temp
RUN mkdir -p /client/log && chmod 755 /client/log


# Запуск с обработкой сигналов
CMD ["python", "-u", "downloader.py"]